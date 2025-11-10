import orjson
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict
import uvicorn

from backend import settings
from backend.services.llm.factory import build_clients, pick_client

def _orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()

app = FastAPI(
    title="Trip App Backend",
    description="智能行程生成系统后端API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------- 1) 设置页：查看已配置的 AI 提供商 -------
@app.get("/api/ai/providers")
async def ai_providers_status():
    """获取已配置的AI提供商状态"""
    clients = build_clients()
    return {
        "primary": settings.LLM_PRIMARY,
        "providers": [
            {"name": k, "configured": True} for k in clients.keys()
        ] + [
            # 也把未配置但支持的列出来
            *[
                {"name": n, "configured": False}
                for n in ["openai", "aliyun", "openrouter", "ollama", "dify"]
                if n not in clients
            ]
        ]
    }

# ------- 2) 对话接口：统一入口 -------
class ChatBody(BaseModel):
    messages: List[Dict[str, str]] = Field(..., description="OpenAI 格式消息")
    provider: str | None = Field(None, description="可选：openai/aliyun/openrouter/ollama/dify")
    model: str | None = None
    temperature: float = 0.7

@app.post("/api/ai/chat")
async def ai_chat(body: ChatBody):
    """统一的AI对话接口"""
    try:
        client = pick_client(body.provider)
        answer = await client.chat(body.messages, model=body.model, temperature=body.temperature)
        return {"provider": client.name, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 注意：原有的Flask路由（如 /api/trips/generate, /api/generate_itinerary 等）
# 仍然在 backend/routes.py 中定义，需要通过Flask应用运行
# 如果需要完全迁移到FastAPI，需要将Flask路由逐步转换为FastAPI路由

if __name__ == '__main__':
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,  # 改为8000以匹配测试命令
        reload=True
    )
