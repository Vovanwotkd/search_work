from sqlalchemy.orm import Session

from app.models import UserProfile, VacancyCache
from app.services.llm import get_llm_service, LLMMessage
from app.services.llm.prompts import VACANCY_MATCH_PROMPT


class VacancyAnalyzer:
    """Service for analyzing vacancy match with user profile."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm_service(db=db)

    async def analyze_match(
        self, profile: UserProfile, vacancy: VacancyCache
    ) -> dict:
        """Analyze how well vacancy matches user profile."""
        # Format profile data
        profile_text = f"""
Позиция: {profile.preferred_position}
Опыт: {profile.experience_years} лет
Навыки: {', '.join(profile.skills or [])}
Зарплата: {profile.preferred_salary_min}-{profile.preferred_salary_max}
Локации: {', '.join(profile.preferred_locations or [])}
О себе: {profile.summary}

Полный профиль: {profile.structured_profile}
"""

        # Format vacancy data
        salary_text = ""
        if vacancy.salary_from or vacancy.salary_to:
            salary_text = f"{vacancy.salary_from or '?'}-{vacancy.salary_to or '?'} {vacancy.salary_currency}"

        vacancy_text = f"""
Должность: {vacancy.title}
Компания: {vacancy.company_name}
Зарплата: {salary_text}
Локация: {vacancy.location}
Опыт: {vacancy.experience}
Тип занятости: {vacancy.employment_type}
Требования: {vacancy.requirements}
Описание: {vacancy.description}
Ключевые навыки: {', '.join(vacancy.key_skills or [])}
"""

        # Analyze with LLM
        prompt = VACANCY_MATCH_PROMPT.format(profile=profile_text, vacancy=vacancy_text)
        llm_messages = [
            LLMMessage(role="system", content="Ты HR-аналитик, оцениваешь соответствие кандидата вакансии."),
            LLMMessage(role="user", content=prompt),
        ]

        result = await self.llm.chat_json(llm_messages)

        # Update vacancy with match data
        vacancy.match_score = result.get("match_score", 0)
        vacancy.match_analysis = result
        self.db.commit()

        return result

    async def batch_analyze(
        self, profile: UserProfile, vacancies: list[VacancyCache]
    ) -> list[dict]:
        """Analyze multiple vacancies."""
        results = []
        for vacancy in vacancies:
            result = await self.analyze_match(profile, vacancy)
            results.append({"vacancy_id": vacancy.id, **result})
        return results
