from sqlalchemy.orm import Session

from app.models import UserProfile, BaseResume, ResumeVariation, VacancyCache, AppSettings
from app.services.llm import get_llm_service, LLMMessage
from app.services.llm.prompts import RESUME_GENERATION_PROMPT, RESUME_ADAPTATION_PROMPT


def get_setting(db: Session, key: str) -> str | None:
    """Get setting value from database."""
    setting = db.query(AppSettings).filter(AppSettings.key == key).first()
    return setting.value if setting else None


class ResumeGenerator:
    """Service for generating and adapting resumes."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm_service(db=db)

    async def generate_base_resume(self, profile: UserProfile) -> BaseResume:
        """Generate base resume from profile."""
        # Format profile
        profile_text = f"""
Позиция: {profile.preferred_position}
Опыт: {profile.experience_years} лет
Навыки: {', '.join(profile.skills or [])}
О себе: {profile.summary}

Полный профиль: {profile.structured_profile}
"""

        # Generate with LLM
        prompt = RESUME_GENERATION_PROMPT.format(profile=profile_text)
        llm_messages = [
            LLMMessage(role="system", content="Ты профессиональный составитель резюме."),
            LLMMessage(role="user", content=prompt),
        ]

        resume_data = await self.llm.chat_json(llm_messages)

        # Add prompt injection if enabled
        resume_data = self._add_prompt_injection(resume_data)

        # Create or update base resume
        base_resume = (
            self.db.query(BaseResume)
            .filter(BaseResume.user_id == profile.user_id, BaseResume.is_active == True)
            .first()
        )

        if not base_resume:
            base_resume = BaseResume(user_id=profile.user_id)
            self.db.add(base_resume)

        base_resume.title = resume_data.get("title", profile.preferred_position)
        base_resume.content = resume_data
        base_resume.is_active = True

        self.db.commit()
        self.db.refresh(base_resume)

        return base_resume

    async def create_variation(
        self,
        base_resume: BaseResume,
        vacancy: VacancyCache,
        profile: UserProfile,
    ) -> ResumeVariation:
        """Create resume variation adapted for specific vacancy."""
        # Format data
        base_resume_text = f"Заголовок: {base_resume.title}\n\nКонтент: {base_resume.content}"

        salary_text = ""
        if vacancy.salary_from or vacancy.salary_to:
            salary_text = f"{vacancy.salary_from or '?'}-{vacancy.salary_to or '?'} {vacancy.salary_currency}"

        vacancy_text = f"""
Должность: {vacancy.title}
Компания: {vacancy.company_name}
Зарплата: {salary_text}
Требования: {vacancy.requirements}
Описание: {vacancy.description}
Ключевые навыки: {', '.join(vacancy.key_skills or [])}
"""

        profile_text = f"""
Навыки: {', '.join(profile.skills or [])}
Опыт: {profile.experience_years} лет
Полный профиль: {profile.structured_profile}
"""

        # Generate adapted resume
        prompt = RESUME_ADAPTATION_PROMPT.format(
            base_resume=base_resume_text,
            vacancy=vacancy_text,
            profile=profile_text,
        )
        llm_messages = [
            LLMMessage(role="system", content="Ты профессиональный составитель резюме."),
            LLMMessage(role="user", content=prompt),
        ]

        result = await self.llm.chat_json(llm_messages)

        # Get resume content
        resume_content = result.get("adapted_resume", base_resume.content)

        # Add prompt injection if enabled
        resume_content = self._add_prompt_injection(resume_content)

        # Create variation
        variation = ResumeVariation(
            base_resume_id=base_resume.id,
            vacancy_id=vacancy.id,
            title=f"{base_resume.title} для {vacancy.company_name}",
            content=resume_content,
            adaptations=result.get("adaptations", []),
            status="draft",
        )

        self.db.add(variation)
        self.db.commit()
        self.db.refresh(variation)

        return variation

    def _add_prompt_injection(self, content: dict | str) -> dict | str:
        """Add prompt injection to resume content if enabled."""
        # Check if injection is enabled
        injection_enabled = get_setting(self.db, "prompt_injection_enabled") == "true"
        if not injection_enabled:
            return content

        # Get injection text
        injection_text = get_setting(self.db, "prompt_injection")
        if not injection_text:
            return content

        # Add injection to content
        if isinstance(content, dict):
            # Add to dict as hidden_metadata field
            content["_ai_metadata"] = injection_text
            # Also inject into summary/about if exists
            if "summary" in content:
                content["summary"] = f"{content['summary']}\n\n{injection_text}"
            elif "about" in content:
                content["about"] = f"{content['about']}\n\n{injection_text}"
        elif isinstance(content, str):
            content = f"{content}\n\n{injection_text}"

        return content
