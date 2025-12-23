from pydantic import BaseModel
from typing import Literal


class SettingsResponse(BaseModel):
    llm_provider: Literal["claude", "openai"]
    llm_model: str | None
    hh_connected: bool
    has_claude_key: bool
    has_openai_key: bool
    available_models: dict[str, list[str]]


class SettingsUpdate(BaseModel):
    llm_provider: Literal["claude", "openai"] | None = None
    llm_model: str | None = None
    claude_api_key: str | None = None
    openai_api_key: str | None = None
