"""Pydantic v2 schemas for chat."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Payload for POST /chat."""

    query: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=36)


class MessageOut(BaseModel):
    """One chat message."""

    role: Literal["user", "ai"]
    content: str
    timestamp: str


class ChatHistoryResponse(BaseModel):
    """Messages of a session."""

    session_id: str
    messages: list[MessageOut]


class SessionOut(BaseModel):
    """Chat session summary for the sidebar."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
