from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Raw interview data
    raw_interview_data = Column(JSON, nullable=True)

    # Structured profile (processed by LLM)
    structured_profile = Column(JSON, nullable=True)

    # Extracted fields for quick access
    skills = Column(JSON, default=list)  # ["Python", "FastAPI", ...]
    experience_years = Column(Integer, nullable=True)
    preferred_position = Column(String(255), nullable=True)
    preferred_salary_min = Column(Integer, nullable=True)
    preferred_salary_max = Column(Integer, nullable=True)
    preferred_locations = Column(JSON, default=list)  # ["Moscow", "Remote"]
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")
