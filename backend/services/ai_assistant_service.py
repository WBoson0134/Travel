"""
AI助手服务
用于处理客户问题和交互
"""
import os
import json
import requests
from typing import List, Dict, Optional
from backend.config import Config
import logging

logger = logging.getLogger(__name__)


class AIAssistantService:
    """AI助手服务：处理客户问答和交互"""
    
    def __init__(self):
        self.openai_api_key = Config.OPENAI_API_KEY
        self.openai_base_url = Config.OPENAI_BASE_URL
        self.dify_api_key = Config.DIFY_API_KEY
        self.dify_api_base = Config.DIFY_API_BASE
        
        # 对话历史存储（实际应用中应使用数据库或Redis）
        self.conversation_history: Dict[str, List[Dict]] = {}
    
    def chat(self, user_id: str, message: str, context: Dict = None) -> Dict:
        """
        处理用户消息并返回AI回复
        
        Args:
            user_id: 用户ID（用于维护对话历史）
            message: 用户消息
            context: 上下文信息（如当前行程、城市等）
        
        Returns:
            AI回复字典，包含回复内容和相关建议
        """
        # 获取或初始化对话历史
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt(context)
        
        # 添加用户消息到历史
        self.conversation_history[user_id].append({
            "role": "user",
            "content": message
        })
        
        # 调用AI服务
        try:
            if self.openai_api_key and self.openai_base_url:
                response = self._chat_with_openai(user_id, system_prompt)
            elif self.dify_api_key and self.dify_api_base:
                response = self._chat_with_dify(user_id, message, context)
            else:
                response = self._chat_fallback(message, context)
            
            # 添加AI回复到历史
            self.conversation_history[user_id].append({
                "role": "assistant",
                "content": response.get("reply", "")
            })
            
            return response
            
        except Exception as e:
            logger.error(f"AI助手服务错误: {e}")
            return {
                "reply": "抱歉，我现在无法回答您的问题。请稍后再试。",
                "suggestions": [],
                "error": str(e)
            }
    
    def _build_system_prompt(self, context: Dict = None) -> str:
        """构建系统提示词"""
        prompt = """你是一个专业的旅游助手，擅长回答关于旅游规划、景点推荐、行程安排等问题。
        
你的职责包括：
1. 回答用户关于旅游的各种问题
2. 提供景点推荐和行程建议
3. 帮助用户优化行程安排
4. 回答关于酒店、交通、美食等旅游相关问题
5. 提供友好的、专业的、有用的建议

请用友好、专业、简洁的方式回答用户问题。"""
        
        if context:
            city = context.get("city")
            if city:
                prompt += f"\n\n当前用户正在规划{city}的旅行。"
            if context.get("days"):
                prompt += f"\n行程天数为{context['days']}天。"
            if context.get("preferences"):
                prompt += f"\n用户偏好：{', '.join(context['preferences'])}。"
        
        return prompt
    
    def _chat_with_openai(self, user_id: str, system_prompt: str) -> Dict:
        """使用OpenAI API进行对话"""
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 添加历史对话（最近10轮）
        history = self.conversation_history[user_id][-20:]  # 最近20条消息
        messages.extend(history)
        
        # 调用OpenAI API
        if "dashscope" in (self.openai_base_url or ""):
            # 阿里云百炼API
            return self._chat_with_dashscope(messages)
        else:
            # 标准OpenAI API
            from openai import OpenAI
            client = OpenAI(
                api_key=self.openai_api_key,
                base_url=self.openai_base_url
            )
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            reply = response.choices[0].message.content
            
            return {
                "reply": reply,
                "suggestions": self._extract_suggestions(reply)
            }
    
    def _chat_with_dashscope(self, messages: List[Dict]) -> Dict:
        """使用阿里云百炼API进行对话"""
        api_url = f"{self.openai_base_url}/services/aigc/text-generation/generation"
        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'qwen-turbo',
            'input': {
                'messages': messages
            },
            'parameters': {
                'temperature': 0.7,
                'max_tokens': 500
            }
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        reply = result.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
        
        return {
            "reply": reply,
            "suggestions": self._extract_suggestions(reply)
        }
    
    def _chat_with_dify(self, user_id: str, message: str, context: Dict = None) -> Dict:
        """使用Dify API进行对话"""
        api_url = f"{self.dify_api_base}/chat-messages"
        headers = {
            'Authorization': f'Bearer {self.dify_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': context or {},
            'query': message,
            'response_mode': 'blocking',
            'conversation_id': user_id,
            'user': user_id
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        reply = result.get('answer', '')
        
        return {
            "reply": reply,
            "suggestions": self._extract_suggestions(reply)
        }
    
    def _chat_fallback(self, message: str, context: Dict = None) -> Dict:
        """回退方案：简单的关键词匹配"""
        message_lower = message.lower()
        
        # 简单的关键词回复
        if any(word in message_lower for word in ['酒店', '住宿', 'hotel']):
            return {
                "reply": "我可以帮您搜索酒店信息。请告诉我您想去的城市和入住日期。",
                "suggestions": ["搜索酒店", "查看酒店评价", "比较价格"]
            }
        elif any(word in message_lower for word in ['景点', '推荐', 'attraction', 'place']):
            return {
                "reply": "我可以为您推荐景点。请告诉我您想去的城市和您的兴趣偏好。",
                "suggestions": ["查看景点列表", "获取景点详情", "规划路线"]
            }
        elif any(word in message_lower for word in ['航班', '机票', 'flight', 'plane']):
            return {
                "reply": "我可以帮您搜索航班信息。请告诉我出发地、目的地和出发日期。",
                "suggestions": ["搜索航班", "比较价格", "查看航班详情"]
            }
        else:
            return {
                "reply": "我是您的旅游助手，可以帮您规划行程、搜索酒店、推荐景点等。请告诉我您需要什么帮助？",
                "suggestions": ["规划行程", "搜索酒店", "推荐景点", "查询航班"]
            }
    
    def _extract_suggestions(self, reply: str) -> List[str]:
        """从回复中提取建议（简单实现）"""
        suggestions = []
        
        # 简单的关键词匹配来提取建议
        if "酒店" in reply or "hotel" in reply.lower():
            suggestions.append("搜索酒店")
        if "景点" in reply or "attraction" in reply.lower():
            suggestions.append("查看景点")
        if "行程" in reply or "itinerary" in reply.lower():
            suggestions.append("生成行程")
        
        return suggestions[:3]  # 最多返回3个建议
    
    def clear_history(self, user_id: str):
        """清除用户的对话历史"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
    
    def get_history(self, user_id: str) -> List[Dict]:
        """获取用户的对话历史"""
        return self.conversation_history.get(user_id, [])

