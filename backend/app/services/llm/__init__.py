from sqlalchemy.orm import Session

from app.services.llm.base import LLMProvider, LLMMessage
from app.services.llm.claude import ClaudeProvider
from app.services.llm.openai import OpenAIProvider
from app.config import settings


# Available models per provider
CLAUDE_MODELS = [
    "claude-sonnet-4-20250514",
    "claude-opus-4-20250514",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
]

OPENAI_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "o1",
    "o1-mini",
    "o1-preview",
]


def _get_db_setting(db: Session, key: str) -> str | None:
    """Get setting from database."""
    from app.models import AppSettings
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    return setting.value if setting else None


def get_llm_service(db: Session = None, provider: str = None, model: str = None, api_key: str = None) -> LLMProvider:
    """Get LLM service based on settings or overrides.

    If db is provided, reads settings from database first, then falls back to env vars.
    """
    # Get provider
    if provider:
        use_provider = provider
    elif db:
        use_provider = _get_db_setting(db, "llm_provider") or settings.llm_provider
    else:
        use_provider = settings.llm_provider

    # Get model
    if model:
        use_model = model
    elif db:
        use_model = _get_db_setting(db, "llm_model") or settings.llm_model or None
    else:
        use_model = settings.llm_model or None

    if use_provider == "claude":
        if api_key:
            key = api_key
        elif db:
            key = _get_db_setting(db, "claude_api_key") or settings.claude_api_key
        else:
            key = settings.claude_api_key
        return ClaudeProvider(api_key=key, model=use_model)
    else:
        if api_key:
            key = api_key
        elif db:
            key = _get_db_setting(db, "openai_api_key") or settings.openai_api_key
        else:
            key = settings.openai_api_key
        return OpenAIProvider(api_key=key, model=use_model)


__all__ = [
    "LLMProvider",
    "LLMMessage",
    "ClaudeProvider",
    "OpenAIProvider",
    "get_llm_service",
    "CLAUDE_MODELS",
    "OPENAI_MODELS",
]
