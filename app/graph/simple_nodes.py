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
from app.utils.constants import DEFAULT_SAFE_REPLY, LEVEL_ORDER
from app.utils.logger import get_logger
from app.utils.validators import normalize_action

logger = get_logger(__name__)

QUESTION_FALLBACKS = [
    ("what_is_goroutine", "Что такое goroutine в Go и зачем она нужна?"),
    ("what_is_channel", "Что такое channel в Go и как он помогает goroutine взаимодействовать?"),
    ("mutex_vs_channel", "Когда в Go лучше использовать mutex, а когда channel?"),
]


def make_ask_question_node(llm_client: OllamaLLMClient):
    def ask_question(state: InterviewState) -> InterviewState:
        state["interview_started"] = True
        state["action"] = "ask_question"

        try:
            content = llm_client.invoke(build_question_messages(state))
            payload = _extract_question_payload(content)
            key = payload.get("question_key", "")
            question = payload.get("question", "")
            if not key or not question:
                raise ValueError("Question JSON misses fields")
        except (LLMClientError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Question generation fallback used: %s", exc)
            key, question = _fallback_question(state)

        state["question_key"] = key
        state["question"] = question
        state["question_index"] = int(state.get("question_index", 0)) + 1
        state["answer"] = ""
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

        if int(state.get("question_index", 0)) >= int(state.get("max_questions", 3)):
            result.action = "finish"
            result.difficulty_change = "keep"

        state["action"] = result.action
        if result.action in {"ask_question", "finish"}:
            _save_round(state)
        if result.action == "ask_question":
            _apply_difficulty_change(state, result.difficulty_change)
        return state

    return decide_next


def run_tool(state: InterviewState) -> InterviewState:
    action = normalize_action(state.get("action", "clarify"))
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
    asked = {item.get("question_key") for item in state.get("history", [])}
    for key, question in QUESTION_FALLBACKS:
        if key not in asked:
            return key, question
    return QUESTION_FALLBACKS[len(asked) % len(QUESTION_FALLBACKS)]


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
    if int(state.get("question_index", 0)) >= int(state.get("max_questions", 3)):
        return DecisionResult(action="finish", difficulty_change="keep", reason="Reached max questions")
    if len(state.get("answer", "").strip()) < 30:
        return DecisionResult(action="clarify", difficulty_change="keep", reason="Answer is too short")
    return DecisionResult(action="ask_question", difficulty_change="keep", reason="Safe fallback continues interview")


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
