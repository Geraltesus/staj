"""Shared LangGraph state definition.

LangGraph passes this mapping between nodes. The service saves the same shape as
JSON, so the state intentionally contains only JSON-serializable values.
"""

from typing import Any, TypedDict


class InterviewState(TypedDict, total=False):
    user_id: int
    chat_id: int
    interview_started: bool
    topic: str
    current_level: str
    max_questions: int
    current_question_index: int
    current_question: str
    current_question_key: str
    current_answer: str
    current_score: int
    current_verdict: str
    current_feedback: str
    current_missing_points: list[str]
    pending_action: str
    last_tool_used: str | None
    tool_result: str
    waiting_for_user_input: bool
    history: list[dict[str, Any]]
    final_summary: str
    strong_sides: list[str]
    weak_sides: list[str]
    improvement_plan: list[str]
    bot_reply: str
    retry_count: int
    error: str


def create_default_state(
    user_id: int,
    chat_id: int,
    topic: str,
    level: str,
    max_questions: int,
) -> InterviewState:
    """Build a fresh interview state for an API user."""

    return {
        "user_id": user_id,
        "chat_id": chat_id,
        "interview_started": False,
        "topic": topic,
        "current_level": level,
        "max_questions": max_questions,
        "current_question_index": 0,
        "current_question": "",
        "current_question_key": "",
        "current_answer": "",
        "current_score": 0,
        "current_verdict": "medium",
        "current_feedback": "",
        "current_missing_points": [],
        "pending_action": "ask_question",
        "last_tool_used": None,
        "tool_result": "",
        "waiting_for_user_input": False,
        "history": [],
        "final_summary": "",
        "strong_sides": [],
        "weak_sides": [],
        "improvement_plan": [],
        "bot_reply": "",
        "retry_count": 0,
        "error": "",
    }
