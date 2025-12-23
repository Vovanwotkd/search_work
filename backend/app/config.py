from pydantic_settings import BaseSettings
from typing import Literal
from pathlib import Path


# Find .env file (in backend/ or parent directory)
def find_env_file():
    current = Path(__file__).parent.parent  # backend/
    for path in [current / ".env", current.parent / ".env"]:
        if path.exists():
            return path
    return None


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # HH.ru OAuth
    hh_client_id: str = ""
    hh_client_secret: str = ""
    hh_redirect_uri: str = "http://localhost:8000/api/auth/hh/callback"

    # LLM
    llm_provider: Literal["claude", "openai"] = "claude"
    claude_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = ""  # If empty, use default for provider

    class Config:
        env_file = find_env_file()
        extra = "ignore"


settings = Settings()
