from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_user, get_current_user_with_hh
from app.models import User, UserProfile, VacancyCache
from app.schemas.vacancy import VacancyResponse, VacancyMatchResponse
from app.services.hh_client import HHClient
from app.services.vacancy_analyzer import VacancyAnalyzer

router = APIRouter()


@router.get("/vacancies")
async def search_vacancies(
    text: Optional[str] = Query(None, description="Search query"),
    area: Optional[str] = Query(None, description="Region ID (1 = Moscow, 2 = SPb)"),
    salary: Optional[int] = Query(None, description="Desired salary"),
    experience: Optional[str] = Query(None, description="Experience level"),
    employment: Optional[str] = Query(None, description="Employment type"),
    schedule: Optional[str] = Query(None, description="Work schedule"),
    page: int = Query(0, ge=0),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Search vacancies on HH.ru."""
    # Use HH client (works without auth for public vacancies)
    client = HHClient(access_token=user.hh_access_token)

    try:
        result = await client.search_vacancies(
            text=text,
            area=area,
            salary=salary,
            experience=experience,
            employment=employment,
            schedule=schedule,
            page=page,
            per_page=per_page,
        )

        # Cache vacancies
        vacancies = []
        for item in result.get("items", []):
            # Check if already cached
            cached = (
                db.query(VacancyCache)
                .filter(VacancyCache.hh_vacancy_id == str(item["id"]))
                .first()
            )

            if not cached:
                cached = VacancyCache(hh_vacancy_id=str(item["id"]))
                db.add(cached)

            # Update cache
            cached.title = item.get("name")
            cached.company_name = item.get("employer", {}).get("name")

            salary_data = item.get("salary") or {}
            cached.salary_from = salary_data.get("from")
            cached.salary_to = salary_data.get("to")
            cached.salary_currency = salary_data.get("currency")

            cached.location = item.get("area", {}).get("name")
            cached.experience = item.get("experience", {}).get("name")
            cached.employment_type = item.get("employment", {}).get("name")

            snippet = item.get("snippet", {})
            cached.requirements = snippet.get("requirement")
            cached.description = snippet.get("responsibility")

            cached.raw_data = item

            vacancies.append(cached)

        db.commit()

        # Return with pagination info
        return {
            "items": [
                {
                    "id": v.id,
                    "hh_vacancy_id": v.hh_vacancy_id,
                    "title": v.title,
                    "company_name": v.company_name,
                    "salary_from": v.salary_from,
                    "salary_to": v.salary_to,
                    "salary_currency": v.salary_currency,
                    "location": v.location,
                    "experience": v.experience,
                    "employment_type": v.employment_type,
                    "requirements": v.requirements,
                    "match_score": v.match_score,
                }
                for v in vacancies
            ],
            "found": result.get("found", 0),
            "page": result.get("page", 0),
            "pages": result.get("pages", 0),
            "per_page": result.get("per_page", 20),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search vacancies: {str(e)}",
        )


@router.get("/vacancies/{vacancy_id}")
async def get_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get vacancy details."""
    vacancy = db.query(VacancyCache).filter(VacancyCache.id == vacancy_id).first()

    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found in cache",
        )

    # Fetch full details from HH if needed
    if not vacancy.description or not vacancy.key_skills:
        client = HHClient(access_token=user.hh_access_token)
        try:
            details = await client.get_vacancy(vacancy.hh_vacancy_id)

            vacancy.description = details.get("description")
            vacancy.requirements = details.get("description")  # Full description
            vacancy.key_skills = [s.get("name") for s in details.get("key_skills", [])]
            vacancy.raw_data = details

            db.commit()
        except Exception:
            pass  # Use cached data if fetch fails

    return vacancy


@router.post("/vacancies/{vacancy_id}/analyze", response_model=VacancyMatchResponse)
async def analyze_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Analyze how well vacancy matches user profile."""
    # Get profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile not found. Complete interview first.",
        )

    # Get vacancy
    vacancy = db.query(VacancyCache).filter(VacancyCache.id == vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found",
        )

    # Fetch full details if needed
    if not vacancy.key_skills:
        client = HHClient(access_token=user.hh_access_token)
        try:
            details = await client.get_vacancy(vacancy.hh_vacancy_id)
            vacancy.description = details.get("description")
            vacancy.key_skills = [s.get("name") for s in details.get("key_skills", [])]
            vacancy.raw_data = details
            db.commit()
        except Exception:
            pass

    # Analyze
    analyzer = VacancyAnalyzer(db)
    result = await analyzer.analyze_match(profile, vacancy)

    return VacancyMatchResponse(
        vacancy_id=vacancy_id,
        match_score=result.get("match_score", 0),
        match_analysis=result,
        matching_skills=result.get("matching_skills", []),
        missing_skills=result.get("missing_skills", []),
        recommendations=result.get("recommendations", []),
    )
