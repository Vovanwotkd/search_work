from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Literal


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Send messages to LLM and get response."""
        pass

    @abstractmethod
    async def chat_json(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> dict:
        """Send messages to LLM and get JSON response."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        pass
