from pydantic import BaseModel
from typing import Literal


class SettingsResponse(BaseModel):
    llm_provider: Literal["claude", "openai"]
    hh_connected: bool
    has_claude_key: bool
    has_openai_key: bool


class SettingsUpdate(BaseModel):
    llm_provider: Literal["claude", "openai"] | None = None
    claude_api_key: str | None = None
    openai_api_key: str | None = None
