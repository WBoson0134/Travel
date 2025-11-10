from abc import ABC, abstractmethod
from typing import List, Dict, Any

Message = Dict[str, str]  # {"role":"user/system/assistant", "content":"..."}


class LLMClient(ABC):
    name: str

    @abstractmethod
    async def chat(self, messages: List[Message], model: str | None = None,
                   temperature: float = 0.7) -> str: ...

