from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class BaseResumeCreate(BaseModel):
    title: str
    content: dict | None = None


class BaseResumeResponse(BaseModel):
    id: int
    title: str | None
    content: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeVariationCreate(BaseModel):
    vacancy_id: int | None = None
    title: str | None = None


class ResumeVariationResponse(BaseModel):
    id: int
    base_resume_id: int
    vacancy_id: int | None
    hh_resume_id: str | None
    title: str | None
    content: dict | None
    adaptations: dict | None
    cover_letter: str | None
    status: Literal["draft", "published", "archived"]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoverLetterGenerate(BaseModel):
    vacancy_id: int
