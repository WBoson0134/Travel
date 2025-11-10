"""
AI助手服务
用于处理客户问题和交互
使用新的LLM服务架构
"""
import asyncio
from typing import List, Dict, Optional
from backend.services.llm import pick_client, Message
import logging

logger = logging.getLogger(__name__)


class AIAssistantService:
    """AI助手服务：处理客户问答和交互"""
    
    def __init__(self):
        # 使用新的LLM服务
        try:
            self.llm_client = pick_client()
            logger.info(f"使用LLM提供商: {self.llm_client.name}")
        except RuntimeError as e:
            logger.warning(f"LLM客户端初始化失败: {e}")
            self.llm_client = None
        
        # 对话历史存储（实际应用中应使用数据库或Redis）
        self.conversation_history: Dict[str, List[Message]] = {}
    
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
            if self.llm_client:
                # 使用新的LLM服务
                messages = self._build_messages(user_id, system_prompt)
                reply = asyncio.run(self.llm_client.chat(messages))
            else:
                reply = self._chat_fallback(message, context).get("reply", "")
            
            # 添加AI回复到历史
            self.conversation_history[user_id].append({
                "role": "assistant",
                "content": reply
            })
            
            return {
                "reply": reply,
                "suggestions": self._extract_suggestions(reply)
            }
            
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
    
    def _build_messages(self, user_id: str, system_prompt: str) -> List[Message]:
        """构建消息列表"""
        messages: List[Message] = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 添加历史对话（最近10轮）
        history = self.conversation_history[user_id][-20:]  # 最近20条消息
        messages.extend(history)
        
        return messages
    
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
    
    def get_history(self, user_id: str) -> List[Message]:
        """获取用户的对话历史"""
        return self.conversation_history.get(user_id, [])
