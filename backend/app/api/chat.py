from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.schemas.chat import ChatSession, ChatMessageCreate, ChatCompleteResponse
from app.services.interview import InterviewService

router = APIRouter()


@router.get("/session", response_model=ChatSession)
async def get_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get current interview session or create new one."""
    service = InterviewService(db)
    session = service.get_or_create_session(user.id)
    return session


@router.post("/message", response_model=ChatSession)
async def send_message(
    message: ChatMessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Send message to interview chat."""
    service = InterviewService(db)
    session = service.get_or_create_session(user.id)

    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is completed. Start a new one with POST /api/chat/reset",
        )

    await service.send_message(session, message.content)
    db.refresh(session)

    return session


@router.post("/complete", response_model=ChatCompleteResponse)
async def complete_interview(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Complete interview and generate profile."""
    service = InterviewService(db)
    session = service.get_or_create_session(user.id)

    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview already completed.",
        )

    if len(session.messages) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough messages to complete interview. Please answer more questions.",
        )

    profile = await service.complete_interview(session)

    return ChatCompleteResponse(
        session_id=session.id,
        profile_created=True,
        message="Interview completed! Profile has been created.",
    )


@router.post("/reset", response_model=ChatSession)
async def reset_interview(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Reset interview and start new one."""
    service = InterviewService(db)
    session = service.reset_session(user.id)
    return session
