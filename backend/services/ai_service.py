import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from backend.services.poi_service import POIService
from backend.services.travel_api_service import TravelAPIService
from backend.services.llm import pick_client
import backend.settings as settings


class AIService:
    """AI服务：用于生成行程、润色描述等"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.poi_service = POIService()
        self.travel_api_service = TravelAPIService()
        try:
            self.llm_client = pick_client(settings.LLM_PRIMARY)
            self.logger.info("AIService using LLM provider: %s", self.llm_client.name)
        except Exception as exc:
            self.logger.warning("LLM provider not configured: %s", exc)
            self.llm_client = None

    # ------------------------------------------------------------------
    # 公开方法
    # ------------------------------------------------------------------
    def generate_trip_plan(self, city: str, days: int, preferences: List[str],
                           pace: str, transport_mode: str, priority: str) -> Dict[str, Any]:
        """生成行程计划：优先使用 LLM + 外部 API，失败时回退到本地算法"""
        base_itinerary = self.poi_service.generate_itinerary(
            city=city,
            days=days,
            preferences=preferences,
            pace=pace,
            transport_mode=transport_mode
        )

        # 酒店候选（如果未配置外部 API 会返回空列表）
        check_in_date = (datetime.now() + timedelta(days=7)).date().isoformat()
        check_out_date = (datetime.now() + timedelta(days=7 + int(days))).date().isoformat()
        hotels = self.travel_api_service.search_hotels(
            city=city,
            check_in=check_in_date,
            check_out=check_out_date
        )

        # 如果未配置 LLM，则直接返回基础行程 + 酒店候选
        if not self.llm_client:
            result = self._deep_copy(base_itinerary)
            if hotels:
                result['recommended_hotels'] = hotels[:5]
            return result

        llm_payload = {
            "request": {
                "city": city,
                "days": days,
                "preferences": preferences,
                "pace": pace,
                "transport_mode": transport_mode,
                "priority": priority
            },
            "base_itinerary": base_itinerary,
            "hotel_candidates": hotels[:8] if hotels else []
        }

        system_prompt = (
            "你是一个资深的旅游行程规划师。"
            "你会根据提供的景点草案、酒店候选和用户偏好，生成详细的行程计划。"
            "请确保时间安排合理、描述生动、活动顺序流畅，并提供贴心提示。"
        )

        user_prompt = (
            "请在以下数据的基础上生成优化后的旅行计划，并严格返回 JSON。\n"
            f"{json.dumps(llm_payload, ensure_ascii=False, indent=2)}\n\n"
            "请输出一个结构化 JSON，至少包含以下字段：city、summary、days、tips。\n"
            "days 为数组，每个元素必须包含 day_number、description、activities；"
            "activities 中的每个活动必须包含 name、type、address、start_time、end_time、"
            "duration_minutes、description、tags、price_range、price_estimate、order。"
            "如有合适的酒店，可在对应 day 中添加 hotel 字段。"
        )
        try:
            response_text = self._chat(system_prompt, user_prompt, temperature=0.65)
            ai_plan = self._safe_parse_json(response_text)
            merged_plan = self._merge_itinerary(base_itinerary, ai_plan, hotels)
            return merged_plan
        except Exception as exc:
            self.logger.error("LLM 生成行程失败: %s", exc, exc_info=True)
            fallback = self._deep_copy(base_itinerary)
            if hotels:
                fallback['recommended_hotels'] = hotels[:5]
            return fallback

    def enhance_description(self, activity_name: str, activity_type: str, city: str) -> str:
        default = f"{activity_name}是{city}的一个著名{activity_type}景点，值得一游。"
        if not self.llm_client:
            return default

        system_prompt = "你是一个专业的旅游文案写手，擅长撰写生动的景点介绍。"
        user_prompt = (
            f"请用迷人的语气介绍 {city} 的 {activity_name} ({activity_type}) ，"
            "包含亮点、适合人群以及小贴士，控制在 80-120 字。"
        )
        try:
            reply = self._chat(system_prompt, user_prompt, temperature=0.8).strip()
            return reply or default
        except Exception as exc:
            self.logger.error("景点描述生成失败: %s", exc, exc_info=True)
            return default

    def adjust_trip(self, current_trip: Dict[str, Any], new_requirements: str) -> Dict[str, Any]:
        if not self.llm_client:
            return current_trip

        system_prompt = "你是一个帮助用户微调旅行计划的专家。"
        user_prompt = (
            "以下是当前行程，请根据用户的新需求进行调整并保持 JSON 结构。\n"
            f"当前行程: {json.dumps(current_trip, ensure_ascii=False, indent=2)}\n"
            f"用户需求: {new_requirements}"
        )
        try:
            reply = self._chat(system_prompt, user_prompt)
            adjusted = self._safe_parse_json(reply)
            if 'days' not in adjusted:
                raise ValueError('调整结果缺少 days 字段')
            return adjusted
        except Exception as exc:
            self.logger.error("调整行程失败: %s", exc, exc_info=True)
            return current_trip

    def get_reviews_summary(self, activity_name: str, city: str) -> Dict[str, Any]:
        default = {
            "rating": 4.5,
            "tags": ["热门", "推荐"],
            "summary": "用户评价普遍较好，是一个值得游览的景点。"
        }
        if not self.llm_client:
            return default

        system_prompt = "你是一名旅游评价分析师。"
        user_prompt = (
            f"请汇总游客对 {city} 的 {activity_name} 的评价，返回 JSON，格式为：\n"
            "{\"rating\": 4.6, \"tags\": [\"标签\"], \"summary\": \"一句话摘要\"}"
        )
        try:
            reply = self._chat(system_prompt, user_prompt, temperature=0.6)
            summary = self._safe_parse_json(reply)
            return {
                "rating": summary.get("rating", default["rating"]),
                "tags": summary.get("tags", default["tags"]),
                "summary": summary.get("summary", default["summary"])
            }
        except Exception as exc:
            self.logger.error("获取景点评价摘要失败: %s", exc, exc_info=True)
            return default

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    def _chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        if not self.llm_client:
            raise RuntimeError("LLM client is not configured")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return asyncio.run(self.llm_client.chat(messages, temperature=temperature))

    def _safe_parse_json(self, text: str) -> Dict[str, Any]:
        if not text:
            raise ValueError("空响应，无法解析 JSON")
        cleaned = text.strip()
        if "```" in cleaned:
            if "```json" in cleaned:
                cleaned = cleaned.split("```json", 1)[1]
            cleaned = cleaned.split("```", 1)[1] if "```" in cleaned else cleaned
        cleaned = cleaned.strip()
        return json.loads(cleaned)

    def _merge_itinerary(self, base: Dict[str, Any], ai_plan: Dict[str, Any], hotels: List[Dict[str, Any]]) -> Dict[str, Any]:
        result = self._deep_copy(base)
        for key in ["city", "summary", "pace", "transport_mode", "total_days"]:
            if ai_plan.get(key):
                result[key] = ai_plan[key]

        ai_days = {day.get('day_number'): day for day in ai_plan.get('days', []) if isinstance(day, dict)}
        merged_days = []
        for base_day in result.get('days', []):
            day_number = base_day.get('day_number')
            ai_day = ai_days.get(day_number)
            if ai_day:
                merged_days.append(self._merge_day(base_day, ai_day))
            else:
                merged_days.append(base_day)
        result['days'] = merged_days

        if hotels:
            result['recommended_hotels'] = hotels[:5]
        if isinstance(ai_plan.get('tips'), list):
            result['tips'] = ai_plan['tips']
        return result

    def _merge_day(self, base_day: Dict[str, Any], ai_day: Dict[str, Any]) -> Dict[str, Any]:
        merged = self._deep_copy(base_day)
        for key in ['description', 'summary', 'theme', 'hotel']:
            if ai_day.get(key):
                merged[key] = ai_day[key]
        merged['activities'] = self._merge_activities(
            base_day.get('activities', []),
            ai_day.get('activities', [])
        )
        return merged

    def _merge_activities(self, base_activities: List[Dict[str, Any]], ai_activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not ai_activities:
            return base_activities
        base_by_order = {act.get('order', idx + 1): act for idx, act in enumerate(base_activities)}
        merged: List[Dict[str, Any]] = []
        used_orders = set()

        for idx, ai_act in enumerate(ai_activities, start=1):
            order = ai_act.get('order', idx)
            base_act = base_by_order.get(order)
            if base_act:
                merged_act = base_act.copy()
                for key, value in ai_act.items():
                    if value not in (None, '', []):
                        merged_act[key] = value
            else:
                merged_act = {
                    'name': ai_act.get('name', f'活动{order}'),
                    'type': ai_act.get('type', '体验'),
                    'address': ai_act.get('address', ''),
                    'start_time': ai_act.get('start_time', '09:00'),
                    'end_time': ai_act.get('end_time', '11:00'),
                    'duration_minutes': ai_act.get('duration_minutes', 120),
                    'description': ai_act.get('description', ''),
                    'tags': ai_act.get('tags', []),
                    'price_range': ai_act.get('price_range', '$$'),
                    'price_estimate': ai_act.get('price_estimate', 50),
                    'order': order
                }
            merged_act.setdefault('order', order)
            merged_act.setdefault('start_time', merged_act.get('start_time', '09:00'))
            merged_act.setdefault('end_time', merged_act.get('end_time', '11:00'))
            merged_act.setdefault('duration_minutes', merged_act.get('duration_minutes', 120))
            merged_act.setdefault('description', merged_act.get('description', ''))
            merged_act.setdefault('tags', merged_act.get('tags', []))
            merged_act.setdefault('price_range', merged_act.get('price_range', '$$'))
            merged_act.setdefault('price_estimate', merged_act.get('price_estimate', 50))
            merged_act.setdefault('type', merged_act.get('type', '体验'))
            merged_act.setdefault('address', merged_act.get('address', ''))
            merged_act.setdefault('name', merged_act.get('name', f'活动{order}'))
            merged.append(merged_act)
            used_orders.add(merged_act['order'])

        for base_act in base_activities:
            order = base_act.get('order')
            if order not in used_orders:
                merged.append(base_act)
        merged.sort(key=lambda x: x.get('order', 0))
        return merged

    def _deep_copy(self, data: Any) -> Any:
        return json.loads(json.dumps(data, ensure_ascii=False))

    # ------------------------------------------------------------------
    # 旧版 mock 方法保留
    # ------------------------------------------------------------------
    def _mock_generate_trip_plan(self, city, days, preferences, pace, transport_mode, priority):
        activities_per_day = 3 if pace == "硬核" else 2 if pace == "中庸" else 1
        days_data = []
        for day in range(1, days + 1):
            activities = []
            for i in range(activities_per_day):
                activities.append({
                    "name": f"{city}景点{day}-{i+1}",
                    "type": preferences[0] if isinstance(preferences, list) and preferences else "文化",
                    "address": f"{city}市某区某街道",
                    "start_time": f"{9+i*3}:00",
                    "end_time": f"{12+i*3}:00",
                    "duration_minutes": 180,
                    "description": f"这是{city}的一个著名景点，值得一游。",
                    "tags": ["推荐", "热门"],
                    "price_range": "$$",
                    "price_estimate": 50.0 * (i + 1),
                    "order": i + 1
                })
            days_data.append({
                "day_number": day,
                "description": f"第{day}天的行程安排",
                "activities": activities
            })
        return {"days": days_data}

