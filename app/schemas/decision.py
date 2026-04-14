"""Pydantic schemas for routing decisions made by the agent."""

from typing import Literal

from pydantic import BaseModel, field_validator

from app.utils.validators import normalize_action, normalize_difficulty_change


class DecisionResult(BaseModel):
    """Structured output returned by the interview manager node."""

    action: Literal["ask_question", "clarify", "generate_hint", "get_reference_answer", "finish"]
    difficulty_change: Literal["up", "keep", "down"] = "keep"
    reason: str

    @field_validator("action", mode="before")
    @classmethod
    def validate_action(cls, value: str) -> str:
        return normalize_action(str(value))

    @field_validator("difficulty_change", mode="before")
    @classmethod
    def validate_difficulty_change(cls, value: str) -> str:
        return normalize_difficulty_change(str(value))
