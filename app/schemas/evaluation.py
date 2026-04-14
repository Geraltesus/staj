"""Pydantic schemas for answer evaluation."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import clamp_score, normalize_verdict


class EvaluationResult(BaseModel):
    """Structured output returned by the answer evaluator node."""

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
