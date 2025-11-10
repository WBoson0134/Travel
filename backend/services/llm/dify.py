import httpx
from typing import List
from .base import LLMClient, Message


class DifyClient(LLMClient):
    """
    Dify 原生接口：POST /v1/chat-messages
    简化实现：只取 blocking 模式的 answer 字段
    """
    def __init__(self, base_url: str, api_key: str, app_user: str):
        self.name = "dify"
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.app_user = app_user

    async def chat(self, messages: List[Message], model: str | None = None,
                   temperature: float = 0.7) -> str:
        # 取最后一条 user 内容作为 query，其余拼成上下文（简化版）
        last_user = ""
        context = []
        for m in messages:
            if m["role"] == "user":
                last_user = m["content"]
            else:
                context.append(m)

        url = f"{self.base_url}/chat-messages"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": {"context": context},   # 供工作流使用（如不需要可省）
            "query": last_user,
            "response_mode": "blocking",
            "user": self.app_user
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            # 常见字段为 "answer"
            return data.get("answer", "")

