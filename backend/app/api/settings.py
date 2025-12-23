from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User, AppSettings
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.config import settings as app_settings

router = APIRouter()


def get_setting(db: Session, key: str) -> str | None:
    """Get setting value from database."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    return setting.value if setting else None


def set_setting(db: Session, key: str, value: str) -> None:
    """Set setting value in database."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = AppSettings(key=key, value=value)
        db.add(setting)
    db.commit()


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get current settings."""
    llm_provider = get_setting(db, "llm_provider") or app_settings.llm_provider

    # Check if API keys are set (in DB or env)
    claude_key_db = get_setting(db, "claude_api_key")
    openai_key_db = get_setting(db, "openai_api_key")

    has_claude = bool(claude_key_db or app_settings.claude_api_key)
    has_openai = bool(openai_key_db or app_settings.openai_api_key)

    return SettingsResponse(
        llm_provider=llm_provider,
        hh_connected=bool(user.hh_access_token),
        has_claude_key=has_claude,
        has_openai_key=has_openai,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update settings."""
    if data.llm_provider:
        set_setting(db, "llm_provider", data.llm_provider)

    if data.claude_api_key:
        set_setting(db, "claude_api_key", data.claude_api_key)

    if data.openai_api_key:
        set_setting(db, "openai_api_key", data.openai_api_key)

    # Return updated settings
    return await get_settings(db=db, user=user)
