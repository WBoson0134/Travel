import httpx
from typing import List, Dict
from .base import LLMClient, Message


class OpenAICompat(LLMClient):
    def __init__(self, base_url: str, api_key: str, default_model: str):
        self.name = "openai_compat"
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model

    async def chat(self, messages: List[Message], model: str | None = None,
                   temperature: float = 0.7) -> str:
        use_model = model or self.default_model
        
        # 处理阿里云百炼的特殊路径
        if "dashscope" in self.base_url or "aliyun" in self.base_url:
            url = f"{self.base_url}/services/aigc/text-generation/generation"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": use_model,
                "input": {
                    "messages": messages
                },
                "parameters": {
                    "temperature": temperature
                }
            }
        else:
            # 标准OpenAI兼容接口
            # 确保base_url正确：https://api.openai.com/v1 -> /v1/chat/completions
            base = self.base_url.rstrip("/")
            if not base.endswith("/v1"):
                # 如果base_url不以/v1结尾，添加它
                base = f"{base}/v1"
            url = f"{base}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": use_model,
                "messages": messages,
                "temperature": temperature
            }
        
        # 对429错误进行指数退避重试
        import asyncio
        import random
        max_retries = 2
        backoff = 1.0
        
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=15) as client:
                try:
                    r = await client.post(url, headers=headers, json=payload)
                except httpx.RequestError as exc:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    raise Exception(f"HTTP request failed: {exc}")
                
                # 检查响应状态
                if r.status_code == 200:
                    data = r.json()
                    # 处理阿里云百炼的响应格式
                    if "dashscope" in self.base_url or "aliyun" in self.base_url:
                        return data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
                    else:
                        # 标准OpenAI格式
                        return data["choices"][0]["message"]["content"]
                
                elif r.status_code == 404:
                    error_msg = f"API endpoint not found (404). URL: {url}. "
                    error_msg += "Check: 1) Base URL is correct (https://api.openai.com/v1 for OpenAI), "
                    error_msg += "2) Model name exists (try gpt-4o-mini), 3) Path is /v1/chat/completions"
                    raise Exception(error_msg)
                
                elif r.status_code == 401:
                    raise Exception("Invalid API key (401). Please check your API key in .env file.")
                
                elif r.status_code == 429:
                    # 429错误：配额不足或速率限制，进行退避重试
                    if attempt < max_retries - 1:
                        error_data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                        error_type = error_data.get("error", {}).get("type", "")
                        
                        if error_type == "insufficient_quota":
                            raise Exception("Insufficient quota (429). Please add credits to your OpenAI account: https://platform.openai.com/account/billing")
                        else:
                            # rate_limit_exceeded: 等待后重试
                            wait_time = backoff + random.random()
                            await asyncio.sleep(wait_time)
                            backoff *= 2
                            continue
                    else:
                        raise Exception("Rate limit exceeded (429). Max retries reached. Please wait and try again later.")
                
                else:
                    # 其他错误
                    error_data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"error": r.text}
                    raise Exception(f"API error ({r.status_code}): {error_data}")
        
        raise RuntimeError("Max retries reached for API request")

