from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime

from app.database import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
