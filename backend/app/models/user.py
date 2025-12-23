from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hh_user_id = Column(String(50), unique=True, nullable=True)
    hh_access_token = Column(Text, nullable=True)
    hh_refresh_token = Column(Text, nullable=True)
    hh_token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    interview_sessions = relationship("InterviewSession", back_populates="user")
    base_resumes = relationship("BaseResume", back_populates="user")
