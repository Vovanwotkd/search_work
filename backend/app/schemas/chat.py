from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class ChatMessage(BaseModel):
    role: Literal["assistant", "user"]
    content: str
    timestamp: datetime | None = None

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    content: str


class ChatSession(BaseModel):
    id: int
    messages: list[ChatMessage]
    status: Literal["in_progress", "completed"]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatCompleteResponse(BaseModel):
    session_id: int
    profile_created: bool
    message: str
