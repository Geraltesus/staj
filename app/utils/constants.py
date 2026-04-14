"""Constants used across the interview workflow."""

DEFAULT_SAFE_REPLY = (
    "Сейчас я не смог корректно обработать шаг интервью. "
    "Попробуйте ответить ещё раз или используйте /reset для нового интервью."
)

OLLAMA_UNAVAILABLE_REPLY = (
    "Модель Ollama пока недоступна. Проверьте, что контейнер ollama запущен "
    "и модель llama3.2:1b уже загружена."
)

ALLOWED_ACTIONS = {"ask_question", "clarify", "generate_hint", "get_reference_answer", "finish"}
ALLOWED_DIFFICULTY_CHANGES = {"up", "keep", "down"}
LEVEL_ORDER = ["junior", "middle", "senior"]
