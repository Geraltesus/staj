"""Prompt templates and message builders for the interview graph."""

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import InterviewState

QUESTION_KEYS = [
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
]

QUESTION_SYSTEM_PROMPT = """
Ты строгий технический интервьюер. Ты проводишь mock interview на русском языке.
Генерируй ровно один вопрос. Вопрос должен соответствовать теме, уровню и истории.
Используй только один из доступных question_key из сообщения пользователя.
Не выбирай первый ключ автоматически: выбери тот, который лучше подходит текущей траектории интервью.
Не повторяй уже заданные вопросы, если есть доступные новые ключи.
Верни короткий JSON: {"question": "...", "question_key": "..."}.
""".strip()

QUESTION_HUMAN_TEMPLATE = """
Тема: {topic}
Уровень: {level}
Уже заданные ключи: {asked_keys}
Доступные question_key: {available_question_keys}
Номер следующего вопроса: {question_number}

Сгенерируй следующий вопрос для кандидата.
""".strip()

EVALUATION_SYSTEM_PROMPT = """
Ты объективный оценщик технического собеседования. Оценивай только ответ кандидата.
Верни JSON строго по схеме: score 0-10, verdict strong|medium|weak, feedback, missing_points.
Пиши feedback на русском языке, коротко и полезно.
""".strip()

EVALUATION_HUMAN_TEMPLATE = """
Тема: {topic}
Уровень: {level}
Вопрос: {question}
Ключ вопроса: {question_key}
Ответ кандидата: {answer}

Оцени ответ. Не задавай новый вопрос.
""".strip()

DECISION_SYSTEM_PROMPT = """
Ты управляющий интервью. Выбери ровно одно следующее действие.
Доступные action: ask_question, clarify, generate_hint, get_reference_answer, finish.
Доступные difficulty_change: up, keep, down.
Если action = ask_question, выбери next_question_key из доступных ключей, учитывая последний ответ, score, feedback, missing_points и всю историю.
Если action не ask_question, верни next_question_key как пустую строку.
Правила:
- finish, если достигнут max_questions или интервью явно пора завершить.
- clarify, если ответ слишком короткий или непонятный и стоит дать кандидату шанс уточнить.
- generate_hint, если кандидат застрял, но вопрос ещё можно спасти.
- get_reference_answer, если нужно показать эталон перед движением дальше.
- ask_question, если можно перейти к следующему вопросу.
Верни JSON: {"action":"...","difficulty_change":"...","next_question_key":"...","reason":"..."}.
""".strip()

DECISION_HUMAN_TEMPLATE = """
Тема: {topic}
Уровень: {level}
Текущий номер вопроса: {question_index}
Максимум вопросов: {max_questions}
Вопрос: {question}
Ответ: {answer}
Оценка: {score}
Вердикт: {verdict}
Feedback: {feedback}
Missing points: {missing_points}
История: {history}
Доступные ещё не заданные question_key: {available_question_keys}

Подсказка для выбора следующего вопроса:
- если кандидат слабее отвечает про concurrency, выбирай goroutine, channel, mutex, map_concurrency или race_condition;
- если слабее отвечает про backend HTTP, выбирай http_handler, middleware или graceful_shutdown;
- если слабее отвечает про основы Go, выбирай defer, interface, error handling или slice;
- если ответ сильный, можно дать вопрос на соседнюю или чуть более сложную тему.

Выбери следующее действие.
""".strip()

REVIEW_SYSTEM_PROMPT = """
Ты наставник по техническим собеседованиям. Дай финальный review на русском языке.
Будь честным, конкретным и поддерживающим.
Верни JSON строго по схеме: summary, strong_sides, weak_sides, improvement_plan.
""".strip()

REVIEW_HUMAN_TEMPLATE = """
Тема: {topic}
Уровень: {level}
История интервью: {history}

Составь итоговый feedback для кандидата.
""".strip()


def build_question_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    asked_keys = [item.get("question_key", "") for item in state.get("history", [])]
    available_question_keys = _rotated_available_question_keys(state, set(asked_keys))
    human = QUESTION_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("level", "junior"),
        asked_keys=asked_keys,
        available_question_keys=available_question_keys,
        question_number=state.get("question_index", 0) + 1,
    )
    return [SystemMessage(content=QUESTION_SYSTEM_PROMPT), HumanMessage(content=human)]


def build_evaluation_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    human = EVALUATION_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("level", "junior"),
        question=state.get("question", ""),
        question_key=state.get("question_key", ""),
        answer=state.get("answer", ""),
    )
    return [SystemMessage(content=EVALUATION_SYSTEM_PROMPT), HumanMessage(content=human)]


def build_decision_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    asked_keys = {item.get("question_key", "") for item in state.get("history", [])}
    available_question_keys = _rotated_available_question_keys(state, asked_keys)
    human = DECISION_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("level", "junior"),
        question_index=state.get("question_index", 0),
        max_questions=state.get("max_questions", 5),
        question=state.get("question", ""),
        answer=state.get("answer", ""),
        score=state.get("score", 0),
        verdict=state.get("verdict", "medium"),
        feedback=state.get("feedback", ""),
        missing_points=state.get("missing_points", []),
        history=state.get("history", []),
        available_question_keys=available_question_keys,
    )
    return [SystemMessage(content=DECISION_SYSTEM_PROMPT), HumanMessage(content=human)]


def _rotated_available_question_keys(state: InterviewState, asked_keys: set[str]) -> list[str]:
    available = [key for key in QUESTION_KEYS if key not in asked_keys]
    if not available:
        return []
    seed = int(state.get("user_id", 0)) * 17 + int(state.get("chat_id", 0)) * 31 + int(state.get("question_index", 0)) * 7
    offset = seed % len(available)
    return available[offset:] + available[:offset]


def build_review_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    human = REVIEW_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("level", "junior"),
        history=state.get("history", []),
    )
    return [SystemMessage(content=REVIEW_SYSTEM_PROMPT), HumanMessage(content=human)]
