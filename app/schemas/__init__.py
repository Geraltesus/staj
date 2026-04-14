
"""Pydantic schemas used by the HTTP API and LLM structured output."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import clamp_score, normalize_action, normalize_difficulty_change, normalize_question_key, normalize_verdict


class StartInterviewRequest(BaseModel):
    user_id: int = Field(description="Stable user/session identifier")
    chat_id: int | None = Field(default=None, description="Optional client conversation id")


class AnswerRequest(BaseModel):
    user_id: int
    chat_id: int | None = None
    text: str = Field(min_length=1)


class InterviewResponse(BaseModel):
    user_id: int
    reply: str
    state: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    transport: str


class EvaluationResult(BaseModel):
    score: int = Field(description="Answer score from 0 to 10")
    verdict: Literal["strong", "medium", "weak"] = "medium"
    feedback: str
    missing_points: list[str] = Field(default_factory=list)

    @field_validator("score", mode="before")
    @classmethod
    def validate_score(cls, value: int) -> int:
        return clamp_score(value)

    @field_validator("verdict", mode="before")
    @classmethod
    def validate_verdict(cls, value: str) -> str:
        return normalize_verdict(str(value))


class DecisionResult(BaseModel):
    action: Literal["ask_question", "clarify", "generate_hint", "get_reference_answer", "finish"]
    difficulty_change: Literal["up", "keep", "down"] = "keep"
    next_question_key: str = ""
    reason: str

    @field_validator("action", mode="before")
    @classmethod
    def validate_action(cls, value: str) -> str:
        return normalize_action(str(value))

    @field_validator("difficulty_change", mode="before")
    @classmethod
    def validate_difficulty_change(cls, value: str) -> str:
        return normalize_difficulty_change(str(value))

    @field_validator("next_question_key", mode="before")
    @classmethod
    def validate_next_question_key(cls, value: str) -> str:
        return normalize_question_key(str(value))


class FinalReviewResult(BaseModel):
    summary: str
    strong_sides: list[str] = Field(default_factory=list)
    weak_sides: list[str] = Field(default_factory=list)
    improvement_plan: list[str] = Field(default_factory=list)
