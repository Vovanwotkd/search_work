from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class VacancyCache(Base):
    __tablename__ = "vacancies_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hh_vacancy_id = Column(String(50), unique=True, nullable=False)

    title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    salary_from = Column(Integer, nullable=True)
    salary_to = Column(Integer, nullable=True)
    salary_currency = Column(String(10), nullable=True)
    location = Column(String(255), nullable=True)
    experience = Column(String(50), nullable=True)
    employment_type = Column(String(50), nullable=True)

    requirements = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    key_skills = Column(JSON, default=list)

    # Match analysis
    match_score = Column(Float, nullable=True)  # 0-100
    match_analysis = Column(JSON, nullable=True)

    raw_data = Column(JSON, nullable=True)  # Full HH API response
    fetched_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    resume_variations = relationship("ResumeVariation", back_populates="vacancy")
