"""HTTP API schemas for the interview mentor service."""

from typing import Any

from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    """Request body for starting or resetting an interview."""

    user_id: int = Field(description="Stable user/session identifier")
    chat_id: int | None = Field(default=None, description="Optional client conversation id")


class AnswerRequest(BaseModel):
    """Request body with the candidate answer for the current question."""

    user_id: int
    chat_id: int | None = None
    text: str = Field(min_length=1)


class InterviewResponse(BaseModel):
    """Response returned to API clients after every interview step."""

    user_id: int
    reply: str
    state: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    transport: str
