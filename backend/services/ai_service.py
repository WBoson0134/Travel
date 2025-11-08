import os
import json
from openai import OpenAI
from backend.config import Config

class AIService:
    """AI服务：用于生成行程、润色描述等"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None
    
    def generate_trip_plan(self, city, days, preferences, pace, transport_mode, priority):
        """生成行程计划"""
        if not self.client:
            return self._mock_generate_trip_plan(city, days, preferences, pace, transport_mode, priority)
        
        prompt = f"""
        请为以下需求生成一个详细的旅游行程计划：
        
        城市：{city}
        天数：{days}天
        兴趣偏好：{', '.join(preferences) if isinstance(preferences, list) else preferences}
        出行节奏：{pace}
        交通方式：{transport_mode}
        优先级：{priority}
        
        请生成一个包含以下信息的详细行程：
        1. 每天的景点/活动安排
        2. 每个景点的推荐理由
        3. 时间安排（考虑营业时间）
        4. 路线顺序（优化路线）
        5. 每个景点的类型标签（自然/美食/文化/购物等）
        6. 预估价格范围
        
        请以JSON格式返回，格式如下：
        {{
            "days": [
                {{
                    "day_number": 1,
                    "description": "第一天的整体描述",
                    "activities": [
                        {{
                            "name": "景点名称",
                            "type": "文化",
                            "address": "地址",
                            "start_time": "09:00",
                            "end_time": "12:00",
                            "duration_minutes": 180,
                            "description": "推荐理由和描述",
                            "tags": ["历史", "必游"],
                            "price_range": "$$",
                            "price_estimate": 50.0,
                            "order": 1
                        }}
                    ]
                }}
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的旅游规划师，擅长制定详细、实用的旅游行程。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            # 尝试提取JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"AI生成失败: {e}")
            return self._mock_generate_trip_plan(city, days, preferences, pace, transport_mode, priority)
    
    def enhance_description(self, activity_name, activity_type, city):
        """润色活动描述"""
        if not self.client:
            return f"{activity_name}是{city}的一个著名{activity_type}景点，值得一游。"
        
        prompt = f"""
        请为以下景点生成一段吸引人的描述和推荐理由：
        景点名称：{activity_name}
        类型：{activity_type}
        城市：{city}
        
        请用自然、有说服力的语言描述这个景点，包括：
        1. 景点的特色和亮点
        2. 为什么值得游览
        3. 适合什么类型的游客
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的旅游文案写手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI润色失败: {e}")
            return f"{activity_name}是{city}的一个著名{activity_type}景点，值得一游。"
    
    def adjust_trip(self, current_trip, new_requirements):
        """根据新需求调整行程"""
        if not self.client:
            return current_trip
        
        prompt = f"""
        现有行程：
        {json.dumps(current_trip, ensure_ascii=False, indent=2)}
        
        用户新需求：{new_requirements}
        
        请根据新需求调整行程，保持JSON格式。
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的旅游规划师，擅长根据用户反馈调整行程。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"AI调整失败: {e}")
            return current_trip
    
    def get_reviews_summary(self, activity_name, city):
        """获取景点评价摘要"""
        if not self.client:
            return {
                "rating": 4.5,
                "tags": ["热门", "推荐"],
                "summary": "用户评价普遍较好，是一个值得游览的景点。"
            }
        
        prompt = f"""
        请为以下景点生成一个综合的用户评价摘要：
        景点名称：{activity_name}
        城市：{city}
        
        请返回JSON格式：
        {{
            "rating": 4.5,
            "tags": ["标签1", "标签2"],
            "summary": "评价摘要"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个旅游评价分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"AI评价失败: {e}")
            return {
                "rating": 4.5,
                "tags": ["热门", "推荐"],
                "summary": "用户评价普遍较好，是一个值得游览的景点。"
            }
    
    def _mock_generate_trip_plan(self, city, days, preferences, pace, transport_mode, priority):
        """模拟生成行程（当没有API key时）"""
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

