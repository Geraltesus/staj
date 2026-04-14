"""Small semantic nodes for the interview LangGraph."""

import json

from app.graph.state import InterviewState
from app.llm.client import LLMClientError, OllamaLLMClient
from app.llm.prompts import (
    build_decision_messages,
    build_evaluation_messages,
    build_question_messages,
    build_review_messages,
)
from app.schemas import DecisionResult, EvaluationResult, FinalReviewResult
from app.services.response_service import ResponseService
from app.tools.local_tools import run_tool as run_local_tool
from app.tools.mcp_client import call_interview_tool
from app.utils.constants import ALLOWED_QUESTION_KEYS, DEFAULT_SAFE_REPLY, LEVEL_ORDER
from app.utils.logger import get_logger
from app.utils.validators import normalize_action

logger = get_logger(__name__)

QUESTION_FALLBACKS = [
    ("what_is_goroutine", "Что такое goroutine в Go и зачем она нужна?"),
    ("what_is_channel", "Что такое channel в Go и как он помогает goroutine взаимодействовать?"),
    ("mutex_vs_channel", "Когда в Go лучше использовать mutex, а когда channel?"),
    ("what_is_context", "Что такое context.Context в Go и зачем он нужен в backend-разработке?"),
    ("defer_usage", "Как работает defer в Go и в каких случаях его удобно использовать?"),
    ("interface_usage", "Что такое interface в Go и как он помогает писать гибкий код?"),
    ("error_handling", "Как в Go принято обрабатывать ошибки и почему их обычно возвращают явно?"),
    ("slice_vs_array", "Чем slice отличается от array в Go?"),
    ("map_concurrency", "Почему обычный map в Go небезопасен для конкурентной записи и как это исправить?"),
    ("http_handler", "Что такое http.Handler в Go и как он используется в HTTP-сервере?"),
    ("middleware", "Что такое middleware в Go HTTP-сервисе и для чего он нужен?"),
    ("graceful_shutdown", "Что такое graceful shutdown HTTP-сервера и зачем он нужен?"),
    ("race_condition", "Что такое race condition и как её искать в Go?"),
]
QUESTION_BY_KEY = dict(QUESTION_FALLBACKS)
CONCURRENCY_QUESTION_KEYS = ["race_condition", "map_concurrency", "mutex_vs_channel", "what_is_channel", "what_is_goroutine"]
HTTP_QUESTION_KEYS = ["http_handler", "middleware", "graceful_shutdown", "what_is_context"]
BASICS_QUESTION_KEYS = ["error_handling", "interface_usage", "defer_usage", "slice_vs_array"]


def make_ask_question_node(llm_client: OllamaLLMClient):
    def ask_question(state: InterviewState) -> InterviewState:
        state["interview_started"] = True
        state["action"] = "ask_question"
        selected_key = state.get("next_question_key", "")

        if _can_use_question_key(state, selected_key):
            key = selected_key
            question = QUESTION_BY_KEY[key]
        else:
            try:
                content = llm_client.invoke(build_question_messages(state))
                payload = _extract_question_payload(content)
                key = payload.get("question_key", "")
                question = payload.get("question", "")
                if not _can_use_question_key(state, key) or not question:
                    raise ValueError("Question JSON misses fields or repeats question")
            except (LLMClientError, ValueError, json.JSONDecodeError) as exc:
                logger.warning("Question generation fallback used: %s", exc)
                key, question = _fallback_question(state)

        state["question_key"] = key
        state["question"] = question
        state["question_index"] = int(state.get("question_index", 0)) + 1
        state["answer"] = ""
        state["next_question_key"] = ""
        state["tool_result"] = ""
        return state

    return ask_question


def make_evaluate_answer_node(llm_client: OllamaLLMClient):
    def evaluate_answer(state: InterviewState) -> InterviewState:
        try:
            result = llm_client.invoke_structured(build_evaluation_messages(state), EvaluationResult)
        except LLMClientError as exc:
            logger.warning("Evaluation fallback used: %s", exc)
            result = _fallback_evaluation(state.get("answer", ""))

        state["score"] = result.score
        state["verdict"] = result.verdict
        state["feedback"] = result.feedback
        state["missing_points"] = result.missing_points
        return state

    return evaluate_answer


def make_decide_next_node(llm_client: OllamaLLMClient):
    def decide_next(state: InterviewState) -> InterviewState:
        try:
            result = llm_client.invoke_structured(build_decision_messages(state), DecisionResult)
        except LLMClientError as exc:
            logger.warning("Decision fallback used: %s", exc)
            result = _fallback_decision(state)

        if int(state.get("question_index", 0)) >= int(state.get("max_questions", 5)):
            result.action = "finish"
            result.difficulty_change = "keep"
            result.next_question_key = ""

        state["action"] = result.action
        if result.action in {"ask_question", "finish"}:
            _save_round(state)
        if result.action == "ask_question":
            _apply_difficulty_change(state, result.difficulty_change)
            state["next_question_key"] = result.next_question_key
            if not _can_use_question_key(state, state["next_question_key"]):
                state["next_question_key"] = _fallback_question(state)[0]
        else:
            state["next_question_key"] = ""
        return state

    return decide_next


async def run_tool(state: InterviewState) -> InterviewState:
    action = normalize_action(state.get("action", "clarify"))
    try:
        state["tool_result"] = await call_interview_tool(action, state)
    except Exception as exc:
        logger.warning("MCP tool call failed, local fallback used: %s", exc)
        state["tool_result"] = run_local_tool(action, state)
    return state


def make_final_review_node(llm_client: OllamaLLMClient):
    def final_review(state: InterviewState) -> InterviewState:
        if state.get("answer"):
            _save_round(state)

        try:
            result = llm_client.invoke_structured(build_review_messages(state), FinalReviewResult)
        except LLMClientError as exc:
            logger.warning("Final review fallback used: %s", exc)
            result = _fallback_review(state)

        state["action"] = "finish"
        state["final_summary"] = result.summary
        state["strong_sides"] = result.strong_sides
        state["weak_sides"] = result.weak_sides
        state["improvement_plan"] = result.improvement_plan
        return state

    return final_review


def respond(state: InterviewState) -> InterviewState:
    response_service = ResponseService()
    action = state.get("action", "ask_question")

    if state.get("final_summary") and action == "finish":
        reply = response_service.final_review(state)
    elif action == "clarify":
        reply = response_service.clarify(state)
    elif action == "generate_hint":
        reply = response_service.hint(state)
    elif action == "get_reference_answer":
        reply = response_service.reference_answer(state)
    elif state.get("question"):
        reply = response_service.question(state)
    else:
        reply = DEFAULT_SAFE_REPLY

    state["bot_reply"] = reply
    return state


def route_input(state: InterviewState) -> str:
    if state.get("action") == "finish":
        return "final_review"
    if not state.get("interview_started"):
        return "ask_question"
    return "evaluate_answer"


def route_decision(state: InterviewState) -> str:
    action = normalize_action(state.get("action", "clarify"))
    if action in {"generate_hint", "get_reference_answer"}:
        return "run_tool"
    if action == "finish":
        return "final_review"
    if action == "ask_question":
        return "ask_question"
    return "respond"


def _save_round(state: InterviewState) -> None:
    history = list(state.get("history", []))
    question_key = state.get("question_key", "")
    already_saved = any(
        item.get("question_index") == state.get("question_index") and item.get("question_key") == question_key
        for item in history
    )
    if not already_saved and question_key and state.get("answer"):
        history.append(
            {
                "question_index": state.get("question_index", 0),
                "question_key": question_key,
                "question": state.get("question", ""),
                "answer": state.get("answer", ""),
                "score": state.get("score", 0),
                "verdict": state.get("verdict", "medium"),
                "feedback": state.get("feedback", ""),
                "missing_points": state.get("missing_points", []),
            }
        )
    state["history"] = history


def _apply_difficulty_change(state: InterviewState, change: str) -> None:
    current = state.get("level", "junior")
    try:
        index = LEVEL_ORDER.index(current)
    except ValueError:
        index = 0

    if change == "up":
        index = min(index + 1, len(LEVEL_ORDER) - 1)
    elif change == "down":
        index = max(index - 1, 0)
    state["level"] = LEVEL_ORDER[index]


def _extract_question_payload(content: str) -> dict:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON in question response")
    return json.loads(content[start : end + 1])


def _fallback_question(state: InterviewState) -> tuple[str, str]:
    available = _available_question_keys(state)
    if not available:
        asked_count = len(state.get("history", []))
        return QUESTION_FALLBACKS[asked_count % len(QUESTION_FALLBACKS)]

    for key in _preferred_question_keys(state):
        if key in available:
            return key, QUESTION_BY_KEY[key]

    key = _rotated_fallback_keys(state, available)[0]
    return key, QUESTION_BY_KEY[key]


def _can_use_question_key(state: InterviewState, question_key: str) -> bool:
    if question_key not in ALLOWED_QUESTION_KEYS:
        return False
    return question_key in _available_question_keys(state)


def _available_question_keys(state: InterviewState) -> list[str]:
    asked = {item.get("question_key") for item in state.get("history", [])}
    return [key for key, _question in QUESTION_FALLBACKS if key not in asked]


def _preferred_question_keys(state: InterviewState) -> list[str]:
    signal = " ".join(
        [
            state.get("question_key", ""),
            state.get("question", ""),
            state.get("answer", ""),
            state.get("feedback", ""),
            " ".join(state.get("missing_points", [])),
        ]
    ).lower()

    if any(word in signal for word in ("goroutine", "channel", "mutex", "race", "concurr", "sync", "map")):
        return CONCURRENCY_QUESTION_KEYS
    if any(word in signal for word in ("http", "server", "request", "handler", "middleware", "shutdown", "context")):
        return HTTP_QUESTION_KEYS
    if any(word in signal for word in ("error", "interface", "slice", "array", "defer", "panic")):
        return BASICS_QUESTION_KEYS
    return []


def _rotated_fallback_keys(state: InterviewState, keys: list[str]) -> list[str]:
    seed = int(state.get("user_id", 0)) * 17 + int(state.get("chat_id", 0)) * 31 + int(state.get("question_index", 0)) * 7
    offset = seed % len(keys)
    return keys[offset:] + keys[:offset]


def _fallback_evaluation(answer: str) -> EvaluationResult:
    if len(answer.strip()) < 30:
        return EvaluationResult(
            score=3,
            verdict="weak",
            feedback="Ответ выглядит слишком коротким. Добавьте определение, назначение и пример.",
            missing_points=["definition", "practical example"],
        )
    return EvaluationResult(
        score=6,
        verdict="medium",
        feedback="Ответ принят, но модель оценки временно недоступна. Продолжим осторожно.",
        missing_points=[],
    )


def _fallback_decision(state: InterviewState) -> DecisionResult:
    if int(state.get("question_index", 0)) >= int(state.get("max_questions", 5)):
        return DecisionResult(action="finish", difficulty_change="keep", next_question_key="", reason="Reached max questions")
    if len(state.get("answer", "").strip()) < 30:
        return DecisionResult(action="clarify", difficulty_change="keep", next_question_key="", reason="Answer is too short")
    next_question_key = _fallback_question(state)[0]
    return DecisionResult(
        action="ask_question",
        difficulty_change="keep",
        next_question_key=next_question_key,
        reason="Safe fallback continues interview",
    )


def _fallback_review(state: InterviewState) -> FinalReviewResult:
    history = state.get("history", [])
    avg_score = 0
    if history:
        avg_score = round(sum(int(item.get("score", 0)) for item in history) / len(history))
    return FinalReviewResult(
        summary=f"Интервью завершено. Средняя оценка: {avg_score}/10. Продолжайте тренировать структурные ответы.",
        strong_sides=["Вы прошли все вопросы MVP-интервью"],
        weak_sides=["Некоторые ответы стоит делать более конкретными"],
        improvement_plan=["Отвечайте по схеме: определение, зачем нужно, пример", "Повторите goroutine, channels и синхронизацию"],
    )
