from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class BaseResume(Base):
    __tablename__ = "base_resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(255), nullable=True)
    content = Column(JSON, nullable=True)  # HH API format structure
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="base_resumes")
    variations = relationship("ResumeVariation", back_populates="base_resume")


class ResumeVariation(Base):
    __tablename__ = "resume_variations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    base_resume_id = Column(Integer, ForeignKey("base_resumes.id"), nullable=False)
    vacancy_id = Column(Integer, ForeignKey("vacancies_cache.id"), nullable=True)

    hh_resume_id = Column(String(50), nullable=True)  # ID on HH after publishing
    title = Column(String(255), nullable=True)
    content = Column(JSON, nullable=True)  # Adapted structure
    adaptations = Column(JSON, nullable=True)  # What was changed and why
    cover_letter = Column(Text, nullable=True)

    # Status: draft, published, archived
    status = Column(String(20), default="draft")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    base_resume = relationship("BaseResume", back_populates="variations")
    vacancy = relationship("VacancyCache", back_populates="resume_variations")
