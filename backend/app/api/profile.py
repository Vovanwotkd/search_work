from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User, UserProfile, BaseResume
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.interview import InterviewService
from app.services.llm import get_llm_service, LLMMessage


class ResumeTextRequest(BaseModel):
    text: str

router = APIRouter()


@router.get("", response_model=ProfileResponse | None)
async def get_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get user profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()

    if not profile:
        return None

    return profile


@router.put("", response_model=ProfileResponse)
async def update_profile(
    update_data: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update user profile manually."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Complete interview first.",
        )

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile


@router.post("/regenerate", response_model=ProfileResponse)
async def regenerate_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Regenerate profile from last completed interview."""
    from app.models import InterviewSession

    # Find last completed interview
    session = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.user_id == user.id,
            InterviewSession.status == "completed",
        )
        .order_by(InterviewSession.updated_at.desc())
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed interview found.",
        )

    # Re-run profile extraction
    service = InterviewService(db)
    # Temporarily set session to in_progress for extraction
    original_status = session.status
    session.status = "in_progress"

    profile = await service.complete_interview(session)

    return profile


@router.post("/parse-resume")
async def parse_resume_text(
    request: ResumeTextRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Parse resume text with LLM and update profile."""
    llm = get_llm_service(db=db)

    # Prompt for extracting profile data from resume text
    extract_prompt = """Проанализируй текст резюме и извлеки информацию в JSON формате:

{
    "preferred_position": "желаемая должность",
    "experience_years": число лет опыта (целое число),
    "skills": ["навык1", "навык2", ...],
    "summary": "краткое описание кандидата (2-3 предложения)",
    "education": "образование",
    "languages": ["язык1", "язык2"],
    "salary_expectation": число или null,
    "work_format": "офис/удалёнка/гибрид или null"
}

Текст резюме:
"""

    messages = [
        LLMMessage(role="system", content="Ты HR-специалист, извлекающий данные из резюме. Отвечай только JSON без markdown."),
        LLMMessage(role="user", content=extract_prompt + request.text),
    ]

    try:
        result = await llm.chat_json(messages)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка разбора резюме: {str(e)}",
        )

    # Get or create profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()

    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    # Update profile with extracted data
    if result.get("preferred_position"):
        profile.preferred_position = result["preferred_position"]
    if result.get("experience_years"):
        profile.experience_years = result["experience_years"]
    if result.get("skills"):
        existing_skills = set(profile.skills or [])
        new_skills = set(result["skills"])
        profile.skills = list(existing_skills | new_skills)
    if result.get("summary"):
        profile.summary = result["summary"]

    # Store full extracted data
    profile.structured_profile = profile.structured_profile or {}
    profile.structured_profile["parsed_resume"] = result
    profile.structured_profile["resume_text"] = request.text[:5000]  # Store first 5000 chars

    db.commit()

    # Also create/update base resume
    base_resume = db.query(BaseResume).filter(
        BaseResume.user_id == user.id,
        BaseResume.is_active == True
    ).first()

    if not base_resume:
        base_resume = BaseResume(user_id=user.id, is_active=True)
        db.add(base_resume)

    base_resume.title = result.get("preferred_position", "Резюме")
    base_resume.content = {
        "parsed_data": result,
        "original_text": request.text[:10000],
    }
    db.commit()

    return {
        "message": "Резюме успешно разобрано",
        "skills_count": len(result.get("skills", [])),
        "position": result.get("preferred_position"),
    }
