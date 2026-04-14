"""Local reference-answer tool backed by JSON data."""

from pathlib import Path

from app.storage.json_store import JsonStore

FALLBACK_REFERENCE = (
    "Эталонный ответ для этого вопроса пока не найден. "
    "Попробуйте сформулировать ответ через определение, назначение и короткий пример."
)


def get_reference_answer(topic: str, level: str, question_key: str) -> str:
    """Return a reference answer from app/tools/data/reference_answers.json."""

    data_path = Path(__file__).parent / "data" / "reference_answers.json"
    data = JsonStore().read(data_path, default={})
    return data.get(topic, {}).get(level, {}).get(question_key, FALLBACK_REFERENCE)
