from sqlalchemy.orm import Session

from app.models import UserProfile, VacancyCache, ResumeVariation
from app.services.llm import get_llm_service, LLMMessage
from app.services.llm.prompts import COVER_LETTER_PROMPT


class CoverLetterService:
    """Service for generating cover letters."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm_service(db=db)

    async def generate(
        self, profile: UserProfile, vacancy: VacancyCache
    ) -> str:
        """Generate cover letter for vacancy."""
        # Format profile
        profile_text = f"""
Позиция: {profile.preferred_position}
Опыт: {profile.experience_years} лет
Навыки: {', '.join(profile.skills or [])}
О себе: {profile.summary}

Полный профиль: {profile.structured_profile}
"""

        # Format vacancy
        salary_text = ""
        if vacancy.salary_from or vacancy.salary_to:
            salary_text = f"{vacancy.salary_from or '?'}-{vacancy.salary_to or '?'} {vacancy.salary_currency}"

        vacancy_text = f"""
Должность: {vacancy.title}
Компания: {vacancy.company_name}
Зарплата: {salary_text}
Локация: {vacancy.location}
Требования: {vacancy.requirements}
Описание: {vacancy.description}
Ключевые навыки: {', '.join(vacancy.key_skills or [])}
"""

        # Generate with LLM
        prompt = COVER_LETTER_PROMPT.format(profile=profile_text, vacancy=vacancy_text)
        llm_messages = [
            LLMMessage(role="system", content="Ты профессиональный карьерный консультант."),
            LLMMessage(role="user", content=prompt),
        ]

        cover_letter = await self.llm.chat(llm_messages, temperature=0.7)
        return cover_letter

    async def generate_for_variation(
        self, variation: ResumeVariation, profile: UserProfile
    ) -> str:
        """Generate cover letter and save to variation."""
        if not variation.vacancy_id:
            raise ValueError("Variation must have vacancy_id to generate cover letter")

        vacancy = self.db.query(VacancyCache).get(variation.vacancy_id)
        if not vacancy:
            raise ValueError("Vacancy not found")

        cover_letter = await self.generate(profile, vacancy)

        variation.cover_letter = cover_letter
        self.db.commit()

        return cover_letter
