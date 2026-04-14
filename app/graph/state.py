"""Shared LangGraph state definition."""

from typing import Any, TypedDict


class InterviewState(TypedDict, total=False):
    user_id: int
    chat_id: int
    interview_started: bool
    topic: str
    level: str
    max_questions: int
    question_index: int
    question: str
    question_key: str
    answer: str
    score: int
    verdict: str
    feedback: str
    missing_points: list[str]
    action: str
    tool_result: str
    history: list[dict[str, Any]]
    final_summary: str
    strong_sides: list[str]
    weak_sides: list[str]
    improvement_plan: list[str]
    bot_reply: str


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
        "level": level,
        "max_questions": max_questions,
        "question_index": 0,
        "question": "",
        "question_key": "",
        "answer": "",
        "score": 0,
        "verdict": "medium",
        "feedback": "",
        "missing_points": [],
        "action": "ask_question",
        "tool_result": "",
        "history": [],
        "final_summary": "",
        "strong_sides": [],
        "weak_sides": [],
        "improvement_plan": [],
        "bot_reply": "",
    }
