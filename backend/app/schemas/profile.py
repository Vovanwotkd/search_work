from pydantic import BaseModel
from datetime import datetime


class ProfileResponse(BaseModel):
    id: int
    skills: list[str]
    experience_years: int | None
    preferred_position: str | None
    preferred_salary_min: int | None
    preferred_salary_max: int | None
    preferred_locations: list[str]
    summary: str | None
    structured_profile: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    skills: list[str] | None = None
    experience_years: int | None = None
    preferred_position: str | None = None
    preferred_salary_min: int | None = None
    preferred_salary_max: int | None = None
    preferred_locations: list[str] | None = None
    summary: str | None = None
