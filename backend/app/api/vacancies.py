from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import re

from app.database import get_db
from app.api.deps import get_current_user, get_current_user_with_hh
from app.models import User, UserProfile, VacancyCache, BaseResume
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
    # Use HH client with refresh token for auto-refresh
    client = HHClient(
        access_token=user.hh_access_token,
        refresh_token=user.hh_refresh_token
    )

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

        # Save new tokens if they were refreshed
        if client.new_tokens:
            user.hh_access_token = client.new_tokens.get("access_token")
            user.hh_refresh_token = client.new_tokens.get("refresh_token")
            db.commit()

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


@router.get("/vacancies/{vacancy_id}", response_model=VacancyResponse)
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
        client = HHClient(
            access_token=user.hh_access_token,
            refresh_token=user.hh_refresh_token
        )
        try:
            details = await client.get_vacancy(vacancy.hh_vacancy_id)

            # Save new tokens if refreshed
            if client.new_tokens:
                user.hh_access_token = client.new_tokens.get("access_token")
                user.hh_refresh_token = client.new_tokens.get("refresh_token")

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
        client = HHClient(
            access_token=user.hh_access_token,
            refresh_token=user.hh_refresh_token
        )
        try:
            details = await client.get_vacancy(vacancy.hh_vacancy_id)

            # Save new tokens if refreshed
            if client.new_tokens:
                user.hh_access_token = client.new_tokens.get("access_token")
                user.hh_refresh_token = client.new_tokens.get("refresh_token")

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


# ============ HH.ru User Info ============


@router.get("/me")
async def get_hh_user_info(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get current user info from HH.ru - raw data for debugging."""
    if not user.hh_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="HH.ru не подключён",
        )

    client = HHClient(
        access_token=user.hh_access_token,
        refresh_token=user.hh_refresh_token,
    )

    try:
        result = await client.get_me()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============ HH.ru Resumes ============


@router.get("/resumes/mine")
async def get_hh_resumes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get user's resumes from HH.ru."""
    if not user.hh_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="HH.ru не подключён. Авторизуйтесь в настройках.",
        )

    client = HHClient(
        access_token=user.hh_access_token,
        refresh_token=user.hh_refresh_token,
    )

    try:
        # Use safer method with detailed error handling
        result = await client.get_resumes_safe()

        resumes = []
        for item in result.get("items", []):
            resumes.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "status": item.get("status", {}).get("name"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
                "url": item.get("alternate_url"),
                "total_views": item.get("total_views", 0),
            })

        return {"resumes": resumes}

    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа к резюме. Возможно, приложение HH.ru не имеет нужных разрешений. Попробуйте переподключить HH.ru в настройках.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки резюме с HH.ru: {error_msg}",
        )


@router.get("/resumes/{resume_id}")
async def get_hh_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get specific resume from HH.ru."""
    if not user.hh_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="HH.ru not connected. Please authorize first.",
        )

    client = HHClient(
        access_token=user.hh_access_token,
        refresh_token=user.hh_refresh_token,
    )

    try:
        resume = await client.get_resume(resume_id)

        # Save new tokens if refreshed
        if client.new_tokens:
            user.hh_access_token = client.new_tokens.get("access_token")
            user.hh_refresh_token = client.new_tokens.get("refresh_token")
            db.commit()

        return resume

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch resume from HH.ru: {str(e)}",
        )


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text)


@router.post("/resumes/{resume_id}/import")
async def import_hh_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Import resume from HH.ru as base resume."""
    if not user.hh_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="HH.ru not connected. Please authorize first.",
        )

    client = HHClient(
        access_token=user.hh_access_token,
        refresh_token=user.hh_refresh_token,
    )

    try:
        hh_resume = await client.get_resume(resume_id)

        # Save new tokens if refreshed
        if client.new_tokens:
            user.hh_access_token = client.new_tokens.get("access_token")
            user.hh_refresh_token = client.new_tokens.get("refresh_token")

        # Deactivate old base resumes
        db.query(BaseResume).filter(
            BaseResume.user_id == user.id,
            BaseResume.is_active == True
        ).update({"is_active": False})

        # Extract skills from HH resume
        skills = [s.get("name") for s in hh_resume.get("skill_set", [])]

        # Extract experience
        experience = []
        for exp in hh_resume.get("experience", []):
            experience.append({
                "company": exp.get("company"),
                "position": exp.get("position"),
                "start": exp.get("start"),
                "end": exp.get("end"),
                "description": strip_html(exp.get("description", "")),
            })

        # Extract education
        education = []
        for edu in hh_resume.get("education", {}).get("primary", []):
            education.append({
                "name": edu.get("name"),
                "organization": edu.get("organization"),
                "result": edu.get("result"),
                "year": edu.get("year"),
            })

        # Create base resume
        base_resume = BaseResume(
            user_id=user.id,
            title=hh_resume.get("title"),
            content={
                "title": hh_resume.get("title"),
                "first_name": hh_resume.get("first_name"),
                "last_name": hh_resume.get("last_name"),
                "birth_date": hh_resume.get("birth_date"),
                "area": hh_resume.get("area", {}).get("name"),
                "salary": hh_resume.get("salary"),
                "skills": skills,
                "experience": experience,
                "education": education,
                "about": strip_html(hh_resume.get("skills", "")),
                "contacts": {
                    "email": next(
                        (c.get("value", {}).get("formatted") for c in hh_resume.get("contact", [])
                         if c.get("type", {}).get("id") == "email"),
                        None
                    ),
                    "phone": next(
                        (c.get("value", {}).get("formatted") for c in hh_resume.get("contact", [])
                         if c.get("type", {}).get("id") == "cell"),
                        None
                    ),
                },
                "hh_resume_id": resume_id,
                "raw_hh_data": hh_resume,
            },
            is_active=True,
        )
        db.add(base_resume)

        # Also update or create user profile with skills
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if profile:
            profile.skills = skills
            profile.preferred_position = hh_resume.get("title")
            if hh_resume.get("salary"):
                profile.preferred_salary_min = hh_resume.get("salary", {}).get("amount")
        else:
            profile = UserProfile(
                user_id=user.id,
                skills=skills,
                preferred_position=hh_resume.get("title"),
                preferred_salary_min=hh_resume.get("salary", {}).get("amount") if hh_resume.get("salary") else None,
            )
            db.add(profile)

        db.commit()
        db.refresh(base_resume)

        return {
            "message": "Resume imported successfully",
            "resume_id": base_resume.id,
            "title": base_resume.title,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import resume: {str(e)}",
        )
