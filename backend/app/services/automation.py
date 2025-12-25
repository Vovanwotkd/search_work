"""Automation service for job search pipeline."""
import asyncio
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models import User, UserProfile, VacancyCache, BaseResume, ResumeVariation
from app.services.hh_client import HHClient
from app.services.vacancy_analyzer import VacancyAnalyzer
from app.services.resume_generator import ResumeGenerator
from app.services.cover_letter import CoverLetterService

logger = logging.getLogger(__name__)

# Global status dict for tracking automation progress
automation_status = {
    "status": "idle",
    "phase": None,
    "message": "",
    "vacancies_loaded": 0,
    "vacancies_total": 0,
    "vacancies_analyzed": 0,
    "resumes_generated": 0,
    "applications_sent": 0,
    "recommendations": [],
    "error": None,
    "should_stop": False,
}


def reset_status():
    """Reset automation status."""
    automation_status.update({
        "status": "idle",
        "phase": None,
        "message": "",
        "vacancies_loaded": 0,
        "vacancies_total": 0,
        "vacancies_analyzed": 0,
        "resumes_generated": 0,
        "applications_sent": 0,
        "recommendations": [],
        "error": None,
        "should_stop": False,
    })


class AutomationService:
    """Service for automated job search pipeline."""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.hh_client = HHClient(
            access_token=user.hh_access_token,
            refresh_token=user.hh_refresh_token,
        )
        self.vacancy_analyzer = VacancyAnalyzer(db)
        self.resume_generator = ResumeGenerator(db)
        self.cover_letter_service = CoverLetterService(db)

    async def run(
        self,
        specializations: list[str],
        cities: list[str],
        auto_apply: bool = True,
        max_resumes: int = 20,
    ):
        """Run the full automation pipeline."""
        reset_status()
        automation_status["status"] = "running"

        try:
            # Phase 1: Load vacancies
            await self._load_vacancies(specializations, cities)
            if automation_status["should_stop"]:
                return

            # Phase 2: Analyze vacancies with LLM
            await self._analyze_vacancies()
            if automation_status["should_stop"]:
                return

            # Phase 3: Generate resumes for top matches
            await self._generate_resumes(max_resumes)
            if automation_status["should_stop"]:
                return

            # Phase 4: Auto-apply if enabled
            if auto_apply:
                await self._auto_apply()

            automation_status["status"] = "completed"
            automation_status["message"] = "Автоматизация успешно завершена!"

        except Exception as e:
            logger.error(f"Automation error: {e}", exc_info=True)
            automation_status["status"] = "error"
            automation_status["error"] = str(e)
            automation_status["message"] = f"Ошибка: {str(e)}"

    async def _load_vacancies(self, specializations: list[str], cities: list[str]):
        """Load vacancies from HH.ru by specializations and cities."""
        automation_status["phase"] = "loading"
        automation_status["message"] = "Загрузка вакансий..."

        all_vacancies = []

        for city_id in cities:
            for spec_id in specializations:
                if automation_status["should_stop"]:
                    return

                try:
                    automation_status["message"] = f"Загрузка: город {city_id}, специализация {spec_id}..."

                    # Search vacancies
                    result = await self.hh_client.search_vacancies(
                        text="",  # No text filter, use specialization
                        area=city_id,
                        specialization=spec_id,
                        per_page=100,
                        page=0,
                    )

                    vacancies = result.get("items", [])
                    total = result.get("found", 0)

                    automation_status["vacancies_total"] += min(total, 100)  # Cap at 100 per query

                    # Save vacancies to cache
                    for vac in vacancies:
                        await self._save_vacancy(vac)
                        all_vacancies.append(vac)
                        automation_status["vacancies_loaded"] += 1

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error loading vacancies for {city_id}/{spec_id}: {e}")
                    continue

        automation_status["message"] = f"Загружено {automation_status['vacancies_loaded']} вакансий"
        logger.info(f"Loaded {len(all_vacancies)} vacancies")

    async def _save_vacancy(self, vacancy_data: dict):
        """Save vacancy to database cache."""
        vacancy_id = str(vacancy_data["id"])

        # Check if already exists
        existing = self.db.query(VacancyCache).filter(VacancyCache.hh_id == vacancy_id).first()
        if existing:
            return existing

        # Extract salary
        salary = vacancy_data.get("salary") or {}

        # Create vacancy cache entry
        vacancy = VacancyCache(
            hh_id=vacancy_id,
            title=vacancy_data.get("name", ""),
            company_name=vacancy_data.get("employer", {}).get("name", ""),
            salary_from=salary.get("from"),
            salary_to=salary.get("to"),
            salary_currency=salary.get("currency", "RUR"),
            requirements=vacancy_data.get("snippet", {}).get("requirement", ""),
            description=vacancy_data.get("snippet", {}).get("responsibility", ""),
            url=vacancy_data.get("alternate_url", ""),
            key_skills=[],  # Will be filled during analysis
            raw_data=vacancy_data,
        )

        self.db.add(vacancy)
        self.db.commit()
        return vacancy

    async def _analyze_vacancies(self):
        """Analyze vacancies with LLM to find best matches."""
        automation_status["phase"] = "analyzing"
        automation_status["message"] = "Анализ вакансий с помощью LLM..."

        # Get user profile
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == self.user.id).first()
        if not profile:
            raise ValueError("User profile not found")

        # Get all unanalyzed vacancies
        vacancies = self.db.query(VacancyCache).filter(
            VacancyCache.match_score == None
        ).limit(200).all()

        recommendations = []

        for vacancy in vacancies:
            if automation_status["should_stop"]:
                return

            try:
                # Analyze match
                analysis = await self.vacancy_analyzer.analyze_match(profile, vacancy)

                # Update vacancy with analysis
                vacancy.match_score = analysis.get("match_score", 0)
                vacancy.match_reasons = analysis.get("reasons", [])
                vacancy.key_skills = analysis.get("required_skills", [])
                self.db.commit()

                automation_status["vacancies_analyzed"] += 1
                automation_status["message"] = f"Проанализировано {automation_status['vacancies_analyzed']} вакансий"

                # Add to recommendations if good match (>60%)
                if vacancy.match_score >= 60:
                    recommendations.append({
                        "vacancy_id": vacancy.hh_id,
                        "title": vacancy.title,
                        "company": vacancy.company_name,
                        "match_score": vacancy.match_score,
                        "reason": "; ".join(analysis.get("reasons", [])[:2]),
                    })

                # Rate limiting for LLM
                await asyncio.sleep(0.2)

            except Exception as e:
                logger.error(f"Error analyzing vacancy {vacancy.id}: {e}")
                continue

        # Sort recommendations by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        automation_status["recommendations"] = recommendations[:50]  # Top 50

        automation_status["message"] = f"Найдено {len(recommendations)} подходящих вакансий"

    async def _generate_resumes(self, max_resumes: int):
        """Generate tailored resumes for top vacancies."""
        automation_status["phase"] = "generating"
        automation_status["message"] = "Генерация резюме..."

        # Get user profile and base resume
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == self.user.id).first()
        base_resume = self.db.query(BaseResume).filter(
            BaseResume.user_id == self.user.id,
            BaseResume.is_active == True
        ).first()

        if not base_resume:
            # Generate base resume first
            automation_status["message"] = "Создание базового резюме..."
            base_resume = await self.resume_generator.generate_base_resume(profile)

        # Get top vacancies by match score
        top_vacancies = self.db.query(VacancyCache).filter(
            VacancyCache.match_score >= 60
        ).order_by(VacancyCache.match_score.desc()).limit(max_resumes).all()

        for vacancy in top_vacancies:
            if automation_status["should_stop"]:
                return

            try:
                # Check if variation already exists
                existing = self.db.query(ResumeVariation).filter(
                    ResumeVariation.vacancy_id == vacancy.id
                ).first()

                if existing:
                    continue

                automation_status["message"] = f"Создание резюме для {vacancy.company_name}..."

                # Generate variation
                await self.resume_generator.create_variation(base_resume, vacancy, profile)

                automation_status["resumes_generated"] += 1

                # Rate limiting
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error generating resume for vacancy {vacancy.id}: {e}")
                continue

        automation_status["message"] = f"Создано {automation_status['resumes_generated']} резюме"

    async def _auto_apply(self):
        """Auto-apply to vacancies."""
        automation_status["phase"] = "applying"
        automation_status["message"] = "Отправка откликов..."

        # Get resume variations with draft status
        variations = self.db.query(ResumeVariation).filter(
            ResumeVariation.status == "draft"
        ).all()

        for variation in variations:
            if automation_status["should_stop"]:
                return

            try:
                vacancy = self.db.query(VacancyCache).filter(VacancyCache.id == variation.vacancy_id).first()
                if not vacancy:
                    continue

                profile = self.db.query(UserProfile).filter(UserProfile.user_id == self.user.id).first()

                # Generate cover letter
                automation_status["message"] = f"Генерация сопроводительного письма для {vacancy.company_name}..."
                cover_letter = await self.cover_letter_service.generate(profile, vacancy)

                # Try to apply via HH.ru API
                # Note: This requires resume to be published on HH.ru first
                try:
                    await self.hh_client.apply_to_vacancy(
                        vacancy_id=vacancy.hh_id,
                        resume_id=None,  # Would need HH resume ID
                        message=cover_letter,
                    )
                    variation.status = "applied"
                    automation_status["applications_sent"] += 1
                except Exception as apply_error:
                    logger.warning(f"Could not auto-apply: {apply_error}")
                    variation.status = "ready"  # Mark as ready for manual apply

                self.db.commit()

                # Rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error applying to vacancy: {e}")
                continue

        automation_status["message"] = f"Отправлено {automation_status['applications_sent']} откликов"
