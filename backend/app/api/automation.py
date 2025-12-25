"""Automation API endpoints."""
import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserProfile, AppSettings
from app.api.auth import get_current_user
from app.services.automation import AutomationService, automation_status
from app.services.github_analyzer import GitHubAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


class AutomationConfig(BaseModel):
    specializations: list[str]
    cities: list[str]
    auto_apply: bool = True
    max_resumes: int = 20


class GitHubRequest(BaseModel):
    username: str


# HH.ru Specializations (IT-related)
HH_SPECIALIZATIONS = [
    {"id": "1", "name": "Информационные технологии"},
    {"id": "1.221", "name": "Программирование, Разработка"},
    {"id": "1.3", "name": "Тестирование"},
    {"id": "1.9", "name": "Системное администрирование"},
    {"id": "1.10", "name": "Сети, телеком"},
    {"id": "1.25", "name": "Data Science"},
    {"id": "1.82", "name": "DevOps"},
    {"id": "1.110", "name": "Машинное обучение"},
    {"id": "1.113", "name": "Информационная безопасность"},
    {"id": "1.117", "name": "Техническая поддержка"},
    {"id": "1.200", "name": "Управление проектами"},
    {"id": "1.211", "name": "Аналитика"},
    {"id": "1.272", "name": "Искусственный интеллект"},
    {"id": "1.327", "name": "CTO, VP"},
    {"id": "1.400", "name": "Продуктовый менеджмент"},
    {"id": "1.420", "name": "Дизайн интерфейсов"},
    {"id": "1.474", "name": "Робототехника"},
    {"id": "1.536", "name": "Технический писатель"},
]

# Major cities
HH_CITIES = [
    {"id": "1", "name": "Москва"},
    {"id": "2", "name": "Санкт-Петербург"},
    {"id": "3", "name": "Екатеринбург"},
    {"id": "4", "name": "Новосибирск"},
    {"id": "41", "name": "Калининград"},
    {"id": "54", "name": "Красноярск"},
    {"id": "66", "name": "Нижний Новгород"},
    {"id": "88", "name": "Казань"},
    {"id": "104", "name": "Воронеж"},
    {"id": "113", "name": "Ростов-на-Дону"},
    {"id": "159", "name": "Самара"},
    {"id": "1438", "name": "Краснодар"},
]


@router.get("/specializations")
async def get_specializations():
    """Get available job specializations."""
    return HH_SPECIALIZATIONS


@router.get("/cities")
async def get_cities():
    """Get available cities for job search."""
    return HH_CITIES


@router.post("/analyze-github")
async def analyze_github(
    request: GitHubRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Analyze GitHub profile to extract skills."""
    analyzer = GitHubAnalyzer()
    try:
        result = await analyzer.analyze(request.username)

        # Update user profile with found skills
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if profile:
            existing_skills = set(profile.skills or [])
            new_skills = set(result["skills"])
            profile.skills = list(existing_skills | new_skills)
            db.commit()

        return result
    except Exception as e:
        logger.error(f"GitHub analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start")
async def start_automation(
    config: AutomationConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Start the automation process."""
    if automation_status.get("status") == "running":
        raise HTTPException(status_code=400, detail="Automation already running")

    # Check if user has profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not found. Complete interview first.")

    # Start automation in background
    service = AutomationService(db, user)
    background_tasks.add_task(
        service.run,
        specializations=config.specializations,
        cities=config.cities,
        auto_apply=config.auto_apply,
        max_resumes=config.max_resumes,
    )

    return {"message": "Automation started"}


@router.post("/stop")
async def stop_automation(
    user: User = Depends(get_current_user),
):
    """Stop the automation process."""
    automation_status["should_stop"] = True
    return {"message": "Stop signal sent"}


@router.get("/status")
async def get_automation_status(
    user: User = Depends(get_current_user),
):
    """Get current automation status."""
    return {
        "status": automation_status.get("status", "idle"),
        "phase": automation_status.get("phase"),
        "message": automation_status.get("message", ""),
        "vacancies_loaded": automation_status.get("vacancies_loaded", 0),
        "vacancies_total": automation_status.get("vacancies_total", 0),
        "vacancies_analyzed": automation_status.get("vacancies_analyzed", 0),
        "resumes_generated": automation_status.get("resumes_generated", 0),
        "applications_sent": automation_status.get("applications_sent", 0),
        "recommendations": automation_status.get("recommendations", []),
        "error": automation_status.get("error"),
    }


@router.get("/recommendations")
async def get_recommendations(
    user: User = Depends(get_current_user),
):
    """Get current vacancy recommendations."""
    return automation_status.get("recommendations", [])
