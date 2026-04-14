"""Local JSON-backed tools used by the interview graph."""

import json
from functools import lru_cache
from pathlib import Path

from app.graph.state import InterviewState

FALLBACK_HINT = (
    "Подсказка для этого вопроса пока не найдена. "
    "Попробуйте ответить по схеме: что это, зачем нужно, где применяется."
)
FALLBACK_REFERENCE = (
    "Эталонный ответ для этого вопроса пока не найден. "
    "Попробуйте сформулировать ответ через определение, назначение и короткий пример."
)


def run_tool(action: str, state: InterviewState) -> str:
    topic = state.get("topic", "golang_backend")
    level = state.get("level", "junior")
    question_key = state.get("question_key", "")

    if action == "generate_hint":
        return generate_hint(topic, level, question_key)
    if action == "get_reference_answer":
        return get_reference_answer(topic, level, question_key)
    return "Инструмент не найден. Попробуем продолжить интервью без него."


def generate_hint(topic: str, level: str, question_key: str) -> str:
    data = _load_json("hints.json")
    return data.get(topic, {}).get(level, {}).get(question_key, FALLBACK_HINT)


def get_reference_answer(topic: str, level: str, question_key: str) -> str:
    data = _load_json("reference_answers.json")
    return data.get(topic, {}).get(level, {}).get(question_key, FALLBACK_REFERENCE)


@lru_cache
def _load_json(filename: str) -> dict:
    path = Path(__file__).parent / "data" / filename
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
