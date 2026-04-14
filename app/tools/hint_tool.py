"""Local hint tool backed by JSON data."""

from pathlib import Path

from app.storage.json_store import JsonStore

FALLBACK_HINT = (
    "Подсказка для этого вопроса пока не найдена. "
    "Попробуйте ответить по схеме: что это, зачем нужно, где применяется."
)


def generate_hint(topic: str, level: str, question_key: str) -> str:
    """Return a hint from app/tools/data/hints.json."""

    data_path = Path(__file__).parent / "data" / "hints.json"
    data = JsonStore().read(data_path, default={})
    return data.get(topic, {}).get(level, {}).get(question_key, FALLBACK_HINT)
