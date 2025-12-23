from app.services.llm.base import LLMProvider, LLMMessage
from app.services.llm.claude import ClaudeProvider
from app.services.llm.openai import OpenAIProvider
from app.config import settings


def get_llm_service() -> LLMProvider:
    """Get LLM service based on current settings."""
    if settings.llm_provider == "claude":
        return ClaudeProvider(api_key=settings.claude_api_key)
    else:
        return OpenAIProvider(api_key=settings.openai_api_key)


__all__ = ["LLMProvider", "LLMMessage", "ClaudeProvider", "OpenAIProvider", "get_llm_service"]
