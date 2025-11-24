import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

from backend.services.poi_service import POIService
from backend.services.travel_api_service import TravelAPIService
from backend.services.llm import pick_client
import backend.settings as settings


class AIService:
    """AI服务：用于生成行程、润色描述等"""

    CACHE_TTL_SECONDS = 6 * 3600  # 6小时缓存

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.poi_service = POIService()
        self.travel_api_service = TravelAPIService()
        self.plan_cache: Dict[Any, Dict[str, Any]] = {}
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
        cache_key = self._cache_key(city, days, preferences, pace, transport_mode, priority)
        cached = self._get_cached_plan(cache_key)
        if cached:
            cache_age = time.time() - cached['timestamp']
            self.logger.info(
                "Returning cached itinerary for %s (age=%.0fs, metrics=%s)",
                cache_key,
                cache_age,
                cached.get("metrics"),
            )
            return self._deep_copy(cached['plan'])

        metrics = {
            "cache_hit": False,
            "meta_duration": 0.0,
            "day_durations": [],
            "llm_calls": 0,
        }
        total_start = time.time()

        base_itinerary = self.poi_service.generate_itinerary(
            city=city,
            days=days,
            preferences=preferences,
            pace=pace,
            transport_mode=transport_mode
        )
        if base_itinerary.get('error'):
            notice = base_itinerary.pop('error')
            base_itinerary.setdefault('notice', notice)
            base_itinerary.setdefault('source', 'baseline')

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
            result['llm_enhanced'] = False
            result['source'] = 'baseline'
            metrics["total_duration"] = time.time() - total_start
            self._set_cached_plan(cache_key, result, metrics)
            return result

        try:
            meta_start = time.time()
            plan_meta = self._generate_plan_meta(
                city=city,
                days=days,
                preferences=preferences,
                pace=pace,
                transport_mode=transport_mode,
                priority=priority,
                base_itinerary=base_itinerary,
                hotels=hotels,
            )
            metrics["meta_duration"] = time.time() - meta_start
            metrics["llm_calls"] += 1

            enhanced_days: List[Dict[str, Any]] = []
            for day in base_itinerary.get('days', []):
                day_start = time.time()
                try:
                    enriched = self._enhance_day_details(
                        city=city,
                        day=day,
                        pace=pace,
                        transport_mode=transport_mode,
                        priority=priority,
                    )
                    metrics["day_durations"].append({
                        "day": day.get('day_number'),
                        "duration": time.time() - day_start
                    })
                    metrics["llm_calls"] += 1
                    if enriched:
                        enhanced_days.append(enriched)
                    else:
                        # 如果返回空，使用原始数据
                        self.logger.warning("Day %s enhancement returned empty, using base data", day.get('day_number'))
                        enhanced_days.append(self._enhance_base_day(day, city))
                except Exception as day_exc:  # pragma: no cover - 防御性
                    self.logger.error("LLM day enhancement failed (day=%s): %s", day.get('day_number'), day_exc, exc_info=True)
                    metrics["day_durations"].append({
                        "day": day.get('day_number'),
                        "duration": time.time() - day_start,
                        "error": str(day_exc)
                    })
                    # 即使失败，也保留基础数据并尝试简单增强
                    enhanced_days.append(self._enhance_base_day(day, city))

            ai_plan = {}
            if plan_meta:
                ai_plan.update({
                    key: plan_meta.get(key)
                    for key in ["city", "summary", "tips", "pace", "transport_mode"]
                    if plan_meta.get(key)
                })
            if enhanced_days:
                ai_plan['days'] = enhanced_days

            merged_plan = self._merge_itinerary(base_itinerary, ai_plan, hotels)
            merged_plan['llm_enhanced'] = True
            merged_plan['source'] = 'llm-split'
            metrics["total_duration"] = time.time() - total_start
            self._set_cached_plan(cache_key, merged_plan, metrics)
            self.logger.info(
                "Split LLM plan generated in %.2fs (meta=%.2fs, day_segments=%s, llm_calls=%s)",
                metrics["total_duration"],
                metrics["meta_duration"],
                metrics["day_durations"],
                metrics["llm_calls"],
            )
            return merged_plan
        except Exception as exc:
            self.logger.error("LLM 生成行程失败: %s", exc, exc_info=True)
            fallback = self._deep_copy(base_itinerary)
            if hotels:
                fallback['recommended_hotels'] = hotels[:5]
            fallback['llm_enhanced'] = False
            fallback['source'] = 'fallback'
            fallback['notice'] = 'AI generation failed, returning baseline itinerary'
            if 'error' in fallback:
                fallback.setdefault('notice', fallback.pop('error'))
            metrics["total_duration"] = time.time() - total_start
            self._set_cached_plan(cache_key, fallback, metrics)
            self.logger.info(
                "Fallback plan returned in %.2fs after %s LLM calls (meta=%.2fs, day_segments=%s)",
                metrics["total_duration"],
                metrics["llm_calls"],
                metrics["meta_duration"],
                metrics["day_durations"],
            )
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
            reply = self._chat(system_prompt, user_prompt, force_json=True)
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
            reply = self._chat(system_prompt, user_prompt, temperature=0.6, force_json=True)
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
    def _generate_plan_meta(
        self,
        city: str,
        days: int,
        preferences: List[str],
        pace: str,
        transport_mode: str,
        priority: str,
        base_itinerary: Dict[str, Any],
        hotels: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        outline = []
        placeholder_mode = (
            base_itinerary.get("source") == "placeholder"
            or not base_itinerary.get("days")
        )
        for day in base_itinerary.get("days", []):
            outline.append({
                "day_number": day.get("day_number"),
                "theme": day.get("theme"),
                "highlights": [
                    {
                        "name": act.get("name"),
                        "start_time": act.get("start_time"),
                        "end_time": act.get("end_time"),
                        "type": act.get("type"),
                    }
                    for act in day.get("activities", [])[:3]
                ]
            })

        payload = {
            "request": {
                "city": city,
                "days": days,
                "preferences": preferences,
                "pace": pace,
                "transport_mode": transport_mode,
                "priority": priority,
            },
            "outline": outline,
            "hotels": [
                {
                    "name": hotel.get("name"),
                    "rating": hotel.get("rating"),
                    "price_range": hotel.get("price_range"),
                }
                for hotel in (hotels or [])[:3]
            ],
            "placeholder": placeholder_mode,
        }

        payload_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

        system_prompt = (
            "你是一名资深旅行策划顾问和文案专家，擅长撰写吸引人、详细的旅行介绍。"
            "你的任务是：\n"
            "1. 撰写生动的总体概述（150-200字），突出城市特色和行程亮点\n"
            "2. 为每一天生成详细的亮点描述（每段50-80字）\n"
            "3. 提供5-8条实用贴士，涵盖交通、美食、购物、注意事项等\n"
            "4. 使用生动的语言，让读者产生向往之情"
        )
        user_prompt = (
            "请根据以下数据生成详细的旅行概要，返回 JSON：\n"
            f"{payload_str}\n\n"
            "输出格式：{\n"
            '  "summary": "总体概述（150-200字）：介绍城市特色、行程亮点、适合人群、最佳体验等",\n'
            '  "daily_highlights": [\n'
            '    {"day_number": 1, "highlight": "第1天详细亮点（50-80字）：描述当天的主题、主要活动、体验价值"},\n'
            '    {"day_number": 2, "highlight": "第2天详细亮点（50-80字）"}\n'
            '  ],\n'
            '  "tips": [\n'
            '    "实用贴士1（交通、美食、购物、注意事项等）",\n'
            '    "实用贴士2",\n'
            '    "实用贴士3",\n'
            '    "实用贴士4",\n'
            '    "实用贴士5"\n'
            '  ]\n'
            "}\n"
            "重要要求：\n"
            "1. summary 必须详细（150-200字），包含城市特色、行程亮点、适合人群\n"
            "2. 每天的 highlight 要具体生动（50-80字），描述主要活动和体验\n"
            "3. tips 要实用具体，涵盖交通、美食、购物、注意事项、最佳时间等\n"
            "4. 如果有推荐酒店，在 tips 中提及\n"
            "5. 使用吸引人的语言，让读者产生向往"
        )
        user_prompt += (
            "务必仅返回一个合法的 JSON 对象，不要附带 Markdown、注释或额外说明。"
        )
        if placeholder_mode:
            user_prompt += (
                " placeholder 为 true 表示当前只是占位草案，请结合城市特色和用户偏好，"
                "重新规划真实、吸引人的景点和体验，并生成详细描述。"
            )

        response_text = self._chat(system_prompt, user_prompt, temperature=0.55, force_json=True)
        try:
            meta = self._safe_parse_json(response_text)
        except Exception as parse_exc:
            self.logger.error("Meta response parse failed: %s; raw=%s", parse_exc, response_text)
            raise

        if "daily_highlights" in meta and "days" not in meta:
            meta["days"] = meta["daily_highlights"]
        meta.setdefault("city", city)
        meta.setdefault("pace", pace)
        meta.setdefault("transport_mode", transport_mode)
        return meta

    def _enhance_day_details(
        self,
        city: str,
        day: Dict[str, Any],
        pace: str,
        transport_mode: str,
        priority: str,
    ) -> Dict[str, Any]:
        minimal_day = {
            "day_number": day.get("day_number"),
            "description": day.get("description"),
            "theme": day.get("theme"),
            "activities": [
                {
                    "name": act.get("name"),
                    "type": act.get("type"),
                    "start_time": act.get("start_time"),
                    "end_time": act.get("end_time"),
                    "tags": act.get("tags", []),
                    "description": act.get("description"),
                    "address": act.get("address"),
                }
                for act in day.get("activities", [])
            ],
        }

        activities = minimal_day.get("activities", [])
        placeholder_mode = (
            not activities or all(
                (not act.get("address")) and act.get("name", "").startswith(city)
                for act in activities
            )
        )

        payload = {
            "city": city,
            "pace": pace,
            "transport_mode": transport_mode,
            "priority": priority,
            "day": minimal_day,
            "placeholder": placeholder_mode,
        }
        payload_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

        system_prompt = (
            "你是一位资深旅行策划师和文案专家，擅长撰写生动、详细、吸引人的旅行体验描述。"
            "你的描述应该：\n"
            "1. 详细描述景点的特色、亮点和体验价值（至少80-120字）\n"
            "2. 包含具体的体验内容、适合人群、最佳游览时间\n"
            "3. 提供实用的贴士和建议（拍照点、注意事项等）\n"
            "4. 使用生动的语言，让读者产生身临其境的感觉\n"
            "5. 为每个活动生成3-5个相关标签\n"
            "6. 提供合理的价格估算（基于活动类型和城市消费水平）"
        )
        user_prompt = (
            "请根据以下行程草案，生成详细的旅行日程，输出 JSON：\n"
            f"{payload_str}\n\n"
            "输出格式：{\n"
            '  "day_number": 1,\n'
            '  "description": "当日详细概述（至少50字，描述当天的主题和亮点）",\n'
            '  "theme": "当日主题（如：文化探索、自然风光、美食体验等）",\n'
            '  "tips": ["实用贴士1", "实用贴士2", "实用贴士3"],\n'
            '  "activities": [\n'
            '    {\n'
            '      "name": "活动名称",\n'
            '      "start_time": "09:00",\n'
            '      "end_time": "11:00",\n'
            '      "description": "详细描述（80-120字）：包含景点特色、体验内容、适合人群、亮点、拍照建议等",\n'
            '      "tags": ["标签1", "标签2", "标签3", "标签4"],\n'
            '      "price_estimate": 100,\n'
            '      "price_range": "$$",\n'
            '      "rating": 4.5,\n'
            '      "address": "详细地址",\n'
            '      "tips": ["小贴士1", "小贴士2"],\n'
            '      "order": 1\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "重要要求：\n"
            "1. 每个活动的 description 必须详细（80-120字），包含具体体验内容\n"
            "2. 每个活动至少3-5个相关标签\n"
            "3. 提供合理的价格估算（基于活动类型）\n"
            "4. 为每个活动添加2-3条实用小贴士\n"
            "5. 当日 description 要生动有趣，至少50字\n"
            "6. 保持原有活动顺序和时间安排"
        )
        user_prompt += "务必仅返回一个合法 JSON 对象，禁止输出 Markdown 代码块或额外文字。"
        if placeholder_mode:
            user_prompt += (
                " 当前活动为占位，请结合城市特色和用户偏好，设计真实、吸引人的体验，"
                "并生成详细描述、实用贴士和合理价格建议。"
            )

        response_text = self._chat(system_prompt, user_prompt, temperature=0.6, force_json=True)
        try:
            result = self._safe_parse_json(response_text)
        except Exception as parse_exc:
            self.logger.error(
                "Day detail parse failed (city=%s day=%s): %s; raw=%s",
                city,
                day.get("day_number"),
                parse_exc,
                response_text,
            )
            raise
        result.setdefault("day_number", day.get("day_number"))
        
        # 增强活动信息：确保每个活动都有完整的字段
        for activity in result.get("activities", []):
            # 从原始数据中补充缺失字段
            if day.get("activities"):
                for orig_act in day.get("activities", []):
                    if orig_act.get("name") == activity.get("name"):
                        # 补充地址和坐标
                        if not activity.get("address"):
                            activity["address"] = orig_act.get("address", "")
                        if not activity.get("latitude"):
                            activity["latitude"] = orig_act.get("latitude")
                        if not activity.get("longitude"):
                            activity["longitude"] = orig_act.get("longitude")
                        # 补充评分
                        if not activity.get("rating"):
                            activity["rating"] = orig_act.get("rating", 4.5)
                        # 补充价格
                        if not activity.get("price_estimate"):
                            activity["price_estimate"] = orig_act.get("price_estimate", 50)
                        break
            
            # 确保有评分
            if not activity.get("rating"):
                activity["rating"] = 4.5
            
            # 确保有价格范围
            if not activity.get("price_range"):
                price = activity.get("price_estimate", 0)
                if price == 0:
                    activity["price_range"] = "免费"
                elif price < 50:
                    activity["price_range"] = "$"
                elif price < 150:
                    activity["price_range"] = "$$"
                elif price < 300:
                    activity["price_range"] = "$$$"
                else:
                    activity["price_range"] = "$$$$"
            
            # 确保有足够的标签（至少3个）
            tags = activity.get("tags", [])
            if len(tags) < 3:
                name = activity.get("name", "").lower()
                desc = activity.get("description", "").lower()
                
                # 根据关键词自动添加标签
                tag_keywords = {
                    "文化": ["文化", "历史", "博物馆", "艺术", "展览", "古迹"],
                    "自然": ["自然", "公园", "海滩", "山", "湖", "风景", "生态"],
                    "美食": ["美食", "餐厅", "小吃", "特色", "品尝", "料理"],
                    "购物": ["购物", "市场", "商店", "纪念品", "特产"],
                    "娱乐": ["娱乐", "表演", "演出", "体验", "互动", "活动"],
                    "亲子": ["亲子", "家庭", "儿童", "适合", "孩子"],
                    "摄影": ["摄影", "拍照", "风景", "美景", "打卡"],
                    "放松": ["放松", "休闲", "悠闲", "舒适", "惬意"],
                    "历史": ["历史", "古迹", "遗址", "传统", "文化"],
                    "现代": ["现代", "时尚", "潮流", "都市", "商业"]
                }
                
                for tag, keywords in tag_keywords.items():
                    if tag not in tags and any(kw in name or kw in desc for kw in keywords):
                        tags.append(tag)
                        if len(tags) >= 5:
                            break
                
                # 如果还不够，添加通用标签
                if len(tags) < 3:
                    tags.extend(["推荐", "热门", "必游"])
                
                activity["tags"] = tags[:5]  # 最多5个标签
            
            # 确保描述足够详细（如果太短，提示需要增强）
            desc = activity.get("description", "")
            if len(desc) < 50:
                self.logger.warning(f"活动 {activity.get('name')} 的描述太短: {len(desc)}字")
        
        return result
    
    def _enhance_base_day(self, day: Dict[str, Any], city: str) -> Dict[str, Any]:
        """在AI增强失败时，对基础数据进行简单增强"""
        enhanced_day = {
            "day_number": day.get("day_number"),
            "description": day.get("description") or f"探索{city}的魅力，体验这座城市的独特风情。",
            "theme": day.get("theme") or "探索",
            "tips": day.get("tips", []),
            "activities": []
        }
        
        # 增强每个活动
        for act in day.get("activities", []):
            enhanced_act = {
                "name": act.get("name", ""),
                "start_time": act.get("start_time", "09:00"),
                "end_time": act.get("end_time", "11:00"),
                "description": act.get("description") or f"{act.get('name', '活动')}是{city}的一个精彩体验，值得一游。",
                "tags": act.get("tags", []) or ["推荐", "热门"],
                "price_estimate": act.get("price_estimate", 50),
                "price_range": act.get("price_range") or "$$",
                "rating": act.get("rating", 4.5),
                "address": act.get("address", ""),
                "latitude": act.get("latitude"),
                "longitude": act.get("longitude"),
                "order": act.get("order", len(enhanced_day["activities"]) + 1)
            }
            
            # 确保有足够的标签
            if len(enhanced_act["tags"]) < 3:
                enhanced_act["tags"].extend(["推荐", "热门", "必游"])
            enhanced_act["tags"] = enhanced_act["tags"][:5]
            
            enhanced_day["activities"].append(enhanced_act)
        
        return enhanced_day

    def _chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, force_json: bool = False) -> str:
        if not self.llm_client:
            raise RuntimeError("LLM client is not configured")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        start_time = time.time()
        result = asyncio.run(self.llm_client.chat(messages, temperature=temperature, force_json=force_json))
        self.logger.info("LLM chat completed in %.2fs", time.time() - start_time)
        return result

    def _safe_parse_json(self, text: str) -> Dict[str, Any]:
        if not text:
            raise ValueError("空响应，无法解析 JSON")
        cleaned = text.strip()
        if "```" in cleaned:
            if "```json" in cleaned:
                cleaned = cleaned.split("```json", 1)[1]
            cleaned = cleaned.split("```", 1)[1] if "```" in cleaned else cleaned
        cleaned = cleaned.strip()
        if not cleaned:
            raise ValueError("空响应，无法解析 JSON")
        if cleaned[0] != "{":
            import re
            match = re.search(r'\{[\s\S]*\}', cleaned)
            if match:
                cleaned = match.group(0)
        if not cleaned or cleaned[0] != "{":
            raise ValueError(f"无法从响应中提取 JSON: {cleaned[:120]}")
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

    def _cache_key(self, city: str, days: int, preferences: List[str], pace: str, transport_mode: str, priority: str):
        pref_key = tuple(sorted(
            [p.strip().lower() for p in (preferences or []) if isinstance(p, str)]
        ))
        return (
            city.strip().lower(),
            int(days),
            pref_key,
            pace.strip().lower() if isinstance(pace, str) else pace,
            transport_mode.strip().lower() if isinstance(transport_mode, str) else transport_mode,
            priority.strip().lower() if isinstance(priority, str) else priority,
        )

    def _get_cached_plan(self, key):
        entry = self.plan_cache.get(key)
        if not entry:
            return None
        if time.time() - entry['timestamp'] > self.CACHE_TTL_SECONDS:
            self.plan_cache.pop(key, None)
            return None
        return entry

    def _set_cached_plan(self, key, plan: Dict[str, Any], metrics: Dict[str, Any]):
        # 简单的容量控制，避免缓存无限增长
        if len(self.plan_cache) > 50:
            oldest_key = min(self.plan_cache.items(), key=lambda item: item[1]['timestamp'])[0]
            self.plan_cache.pop(oldest_key, None)
        self.plan_cache[key] = {
            "plan": self._deep_copy(plan),
            "timestamp": time.time(),
            "metrics": metrics,
        }

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

