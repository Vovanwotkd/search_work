import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import InterviewSession, UserProfile, User, AppSettings
from app.services.llm import get_llm_service, LLMMessage
from app.services.llm.prompts import (
    INTERVIEW_SYSTEM_PROMPT,
    INTERVIEW_FIRST_MESSAGE,
    PROFILE_EXTRACTION_PROMPT,
)

logger = logging.getLogger(__name__)


def get_setting(db: Session, key: str) -> str | None:
    """Get setting value from database."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    return setting.value if setting else None


class InterviewService:
    """Service for conducting LLM-powered interviews."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm_service(db=db)

    def get_or_create_session(self, user_id: int) -> InterviewSession:
        """Get active session or create new one."""
        # Try to find existing in_progress session
        session = (
            self.db.query(InterviewSession)
            .filter(
                InterviewSession.user_id == user_id,
                InterviewSession.status == "in_progress",
            )
            .first()
        )

        if session:
            return session

        # Get custom first message or use default
        first_message = get_setting(self.db, "prompt_interview_first") or INTERVIEW_FIRST_MESSAGE

        # Create new session with first message
        session = InterviewSession(
            user_id=user_id,
            messages=[
                {
                    "role": "assistant",
                    "content": first_message,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
            status="in_progress",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    async def send_message(self, session: InterviewSession, user_message: str) -> str:
        """Process user message and get LLM response."""
        logger.info(f"Processing message for session {session.id}: {user_message[:50]}...")

        # Add user message to history
        messages = list(session.messages or [])
        messages.append(
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Build LLM messages with custom or default system prompt
        system_prompt = get_setting(self.db, "prompt_interview_system") or INTERVIEW_SYSTEM_PROMPT
        llm_messages = [LLMMessage(role="system", content=system_prompt)]
        for msg in messages:
            llm_messages.append(LLMMessage(role=msg["role"], content=msg["content"]))

        # Get LLM response
        try:
            logger.info(f"Calling LLM ({self.llm.provider_name}, model: {self.llm.model})...")
            response = await self.llm.chat(llm_messages)
            logger.info(f"LLM response received: {response[:50]}...")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

        # Add assistant response to history
        messages.append(
            {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Update session
        session.messages = messages
        session.updated_at = datetime.utcnow()
        self.db.commit()
        logger.info(f"Session updated, total messages: {len(messages)}")

        return response

    async def complete_interview(self, session: InterviewSession) -> UserProfile:
        """Complete interview and generate profile."""
        # Build interview history string
        history_parts = []
        for msg in session.messages:
            role = "Кандидат" if msg["role"] == "user" else "Интервьюер"
            history_parts.append(f"{role}: {msg['content']}")
        interview_history = "\n\n".join(history_parts)

        # Extract profile using LLM
        prompt = PROFILE_EXTRACTION_PROMPT.format(interview_history=interview_history)
        llm_messages = [
            LLMMessage(role="system", content="Ты HR-аналитик. Извлекай структурированные данные из интервью."),
            LLMMessage(role="user", content=prompt),
        ]

        profile_data = await self.llm.chat_json(llm_messages)

        # Create or update user profile
        profile = (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == session.user_id)
            .first()
        )

        if not profile:
            profile = UserProfile(user_id=session.user_id)
            self.db.add(profile)

        # Update profile fields
        profile.raw_interview_data = session.messages
        profile.structured_profile = profile_data
        profile.skills = profile_data.get("skills", [])
        profile.experience_years = profile_data.get("experience_years")
        profile.preferred_position = profile_data.get("preferred_position")
        profile.preferred_salary_min = profile_data.get("preferred_salary_min")
        profile.preferred_salary_max = profile_data.get("preferred_salary_max")
        profile.preferred_locations = profile_data.get("preferred_locations", [])
        profile.summary = profile_data.get("summary")
        profile.updated_at = datetime.utcnow()

        # Mark session as completed
        session.status = "completed"
        session.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(profile)

        return profile

    def reset_session(self, user_id: int) -> InterviewSession:
        """Reset interview - mark old as completed and create new."""
        # Mark existing sessions as completed
        self.db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id,
            InterviewSession.status == "in_progress",
        ).update({"status": "completed"})
        self.db.commit()

        # Create new session
        return self.get_or_create_session(user_id)
