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
ALLOWED_QUESTION_KEYS = {
    "what_is_goroutine",
    "what_is_channel",
    "mutex_vs_channel",
    "what_is_context",
    "defer_usage",
    "interface_usage",
    "error_handling",
    "slice_vs_array",
    "map_concurrency",
    "http_handler",
    "middleware",
    "graceful_shutdown",
    "race_condition",
}
