from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User, UserProfile
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.interview import InterviewService

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
