from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user, get_current_user_with_hh
from app.models import User, UserProfile, BaseResume, ResumeVariation, VacancyCache
from app.schemas.resume import (
    BaseResumeResponse,
    BaseResumeCreate,
    ResumeVariationResponse,
    ResumeVariationCreate,
)
from app.services.resume_generator import ResumeGenerator
from app.services.cover_letter import CoverLetterService
from app.services.hh_client import HHClient

router = APIRouter()


# ============ Base Resume ============


@router.get("/base", response_model=BaseResumeResponse | None)
async def get_base_resume(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get base resume."""
    resume = (
        db.query(BaseResume)
        .filter(BaseResume.user_id == user.id, BaseResume.is_active == True)
        .first()
    )
    return resume


@router.post("/base", response_model=BaseResumeResponse)
async def create_base_resume(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate base resume from profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile not found. Complete interview first.",
        )

    generator = ResumeGenerator(db)
    resume = await generator.generate_base_resume(profile)

    return resume


@router.put("/base", response_model=BaseResumeResponse)
async def update_base_resume(
    data: BaseResumeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update base resume manually."""
    resume = (
        db.query(BaseResume)
        .filter(BaseResume.user_id == user.id, BaseResume.is_active == True)
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base resume not found. Create one first.",
        )

    resume.title = data.title
    if data.content:
        resume.content = data.content

    db.commit()
    db.refresh(resume)

    return resume


# ============ Resume Variations ============


@router.get("/variations", response_model=list[ResumeVariationResponse])
async def list_variations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all resume variations."""
    base_resume = (
        db.query(BaseResume)
        .filter(BaseResume.user_id == user.id, BaseResume.is_active == True)
        .first()
    )

    if not base_resume:
        return []

    variations = (
        db.query(ResumeVariation)
        .filter(ResumeVariation.base_resume_id == base_resume.id)
        .order_by(ResumeVariation.created_at.desc())
        .all()
    )

    return variations


@router.post("/variations", response_model=ResumeVariationResponse)
async def create_variation(
    data: ResumeVariationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create resume variation for specific vacancy."""
    # Get profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile not found.",
        )

    # Get base resume
    base_resume = (
        db.query(BaseResume)
        .filter(BaseResume.user_id == user.id, BaseResume.is_active == True)
        .first()
    )
    if not base_resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Base resume not found. Create one first.",
        )

    # Get vacancy
    if not data.vacancy_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vacancy_id is required.",
        )

    vacancy = db.query(VacancyCache).filter(VacancyCache.id == data.vacancy_id).first()
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vacancy not found.",
        )

    # Generate variation
    generator = ResumeGenerator(db)
    variation = await generator.create_variation(base_resume, vacancy, profile)

    return variation


@router.get("/variations/{variation_id}", response_model=ResumeVariationResponse)
async def get_variation(
    variation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get resume variation."""
    variation = db.query(ResumeVariation).filter(ResumeVariation.id == variation_id).first()

    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variation not found.",
        )

    return variation


@router.delete("/variations/{variation_id}")
async def delete_variation(
    variation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete resume variation."""
    variation = db.query(ResumeVariation).filter(ResumeVariation.id == variation_id).first()

    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variation not found.",
        )

    db.delete(variation)
    db.commit()

    return {"message": "Variation deleted"}


@router.post("/variations/{variation_id}/cover-letter")
async def generate_cover_letter(
    variation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate cover letter for variation."""
    variation = db.query(ResumeVariation).filter(ResumeVariation.id == variation_id).first()
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variation not found.",
        )

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile not found.",
        )

    service = CoverLetterService(db)
    cover_letter = await service.generate_for_variation(variation, profile)

    return {"cover_letter": cover_letter}


@router.post("/variations/{variation_id}/publish")
async def publish_variation(
    variation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_with_hh),
):
    """Publish variation to HH.ru."""
    variation = db.query(ResumeVariation).filter(ResumeVariation.id == variation_id).first()
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variation not found.",
        )

    # Prepare HH resume data
    content = variation.content or {}

    # This is a simplified version - real HH API requires specific format
    hh_resume_data = {
        "title": variation.title or content.get("title"),
        # Add more fields as needed based on HH API requirements
    }

    client = HHClient(
        access_token=user.hh_access_token,
        refresh_token=user.hh_refresh_token
    )

    try:
        if variation.hh_resume_id:
            # Update existing
            result = await client.update_resume(variation.hh_resume_id, hh_resume_data)
        else:
            # Create new
            result = await client.create_resume(hh_resume_data)
            variation.hh_resume_id = result.get("id")

        # Save new tokens if refreshed
        if client.new_tokens:
            user.hh_access_token = client.new_tokens.get("access_token")
            user.hh_refresh_token = client.new_tokens.get("refresh_token")

        variation.status = "published"
        db.commit()

        return {"message": "Resume published", "hh_resume_id": variation.hh_resume_id}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish resume: {str(e)}",
        )
