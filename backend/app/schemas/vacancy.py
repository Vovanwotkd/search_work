from pydantic import BaseModel
from datetime import datetime


class VacancySearchParams(BaseModel):
    text: str | None = None
    area: str | None = None  # Region ID
    salary: int | None = None
    experience: str | None = None  # noExperience, between1And3, between3And6, moreThan6
    employment: str | None = None  # full, part, project, volunteer, probation
    schedule: str | None = None  # fullDay, shift, flexible, remote
    page: int = 0
    per_page: int = 20


class VacancySalary(BaseModel):
    from_: int | None = None
    to: int | None = None
    currency: str | None = None

    class Config:
        populate_by_name = True
        fields = {"from_": {"alias": "from"}}


class VacancyResponse(BaseModel):
    id: int
    hh_vacancy_id: str
    title: str | None
    company_name: str | None
    salary_from: int | None
    salary_to: int | None
    salary_currency: str | None
    location: str | None
    experience: str | None
    employment_type: str | None
    requirements: str | None
    description: str | None
    key_skills: list[str]
    match_score: float | None
    fetched_at: datetime

    class Config:
        from_attributes = True


class VacancyMatchResponse(BaseModel):
    vacancy_id: int
    match_score: float
    match_analysis: dict
    matching_skills: list[str]
    missing_skills: list[str]
    recommendations: list[str]
