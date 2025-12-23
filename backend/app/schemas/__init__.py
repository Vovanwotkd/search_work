from app.schemas.chat import ChatMessage, ChatSession, ChatMessageCreate, ChatCompleteResponse
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.schemas.vacancy import VacancyResponse, VacancySearchParams, VacancyMatchResponse
from app.schemas.resume import (
    BaseResumeResponse,
    BaseResumeCreate,
    ResumeVariationResponse,
    ResumeVariationCreate,
)
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.schemas.auth import AuthStatus, HHTokenResponse

__all__ = [
    "ChatMessage",
    "ChatSession",
    "ChatMessageCreate",
    "ChatCompleteResponse",
    "ProfileResponse",
    "ProfileUpdate",
    "VacancyResponse",
    "VacancySearchParams",
    "VacancyMatchResponse",
    "BaseResumeResponse",
    "BaseResumeCreate",
    "ResumeVariationResponse",
    "ResumeVariationCreate",
    "SettingsResponse",
    "SettingsUpdate",
    "AuthStatus",
    "HHTokenResponse",
]
