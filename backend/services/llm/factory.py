from typing import Dict
from .base import LLMClient
from .openai_compat import OpenAICompat
from .dify import DifyClient
import backend.settings as settings


def build_clients() -> Dict[str, LLMClient]:
    clients: Dict[str, LLMClient] = {}

    # OpenAI 兼容（含阿里云百炼兼容、OpenRouter、Ollama、真·OpenAI等）
    if settings.OPENAI_BASE_URL and settings.OPENAI_API_KEY:
        clients["openai"]  = OpenAICompat(settings.OPENAI_BASE_URL, settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
        clients["aliyun"]  = clients["openai"]       # 逻辑别名：如果你把 BASE_URL 指向百炼兼容端
        clients["openrouter"] = clients["openai"]    # 同理
        clients["ollama"]  = clients["openai"]       # 同理

    # Dify 原生
    if settings.DIFY_API_BASE and settings.DIFY_API_KEY:
        clients["dify"] = DifyClient(settings.DIFY_API_BASE, settings.DIFY_API_KEY, settings.DIFY_APP_USER)

    return clients


def pick_client(prefer: str | None = None) -> LLMClient:
    clients = build_clients()
    if prefer and prefer in clients:
        return clients[prefer]
    # 默认选择
    if settings.LLM_PRIMARY in clients:
        return clients[settings.LLM_PRIMARY]
    # 兜底任选一个
    if clients:
        return next(iter(clients.values()))
    raise RuntimeError("No LLM providers configured")

