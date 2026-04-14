"""Validation and normalization helpers for model outputs."""

from app.utils.constants import ALLOWED_ACTIONS, ALLOWED_DIFFICULTY_CHANGES, ALLOWED_QUESTION_KEYS


def clamp_score(score: int) -> int:
    """Normalize a model score to the 0..10 interval."""

    return max(0, min(10, int(score)))


def normalize_verdict(verdict: str) -> str:
    return verdict if verdict in {"strong", "medium", "weak"} else "medium"


def normalize_action(action: str) -> str:
    return action if action in ALLOWED_ACTIONS else "clarify"


def normalize_difficulty_change(change: str) -> str:
    return change if change in ALLOWED_DIFFICULTY_CHANGES else "keep"


def normalize_question_key(question_key: str) -> str:
    return question_key if question_key in ALLOWED_QUESTION_KEYS else ""
