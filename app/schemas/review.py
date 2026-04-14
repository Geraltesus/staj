"""Pydantic schemas for the final interview review."""

from pydantic import BaseModel, Field


class FinalReviewResult(BaseModel):
    """Structured output returned by the final mentor node."""

    summary: str
    strong_sides: list[str] = Field(default_factory=list)
    weak_sides: list[str] = Field(default_factory=list)
    improvement_plan: list[str] = Field(default_factory=list)
