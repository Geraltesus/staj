"""Question generation node."""

import json

from app.graph.state import InterviewState
from app.llm.client import LLMClientError, OllamaLLMClient
from app.llm.message_factory import build_question_messages
from app.utils.logger import get_logger

logger = get_logger(__name__)

QUESTION_FALLBACKS = [
    ("what_is_goroutine", "Что такое goroutine в Go и зачем она нужна?"),
    ("what_is_channel", "Что такое channel в Go и как он помогает goroutine взаимодействовать?"),
    ("mutex_vs_channel", "Когда в Go лучше использовать mutex, а когда channel?"),
]


def make_generate_question_node(llm_client: OllamaLLMClient):
    def generate_question(state: InterviewState) -> InterviewState:
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

        state["current_question_key"] = key
        state["current_question"] = question
        state["current_question_index"] = int(state.get("current_question_index", 0)) + 1
        state["current_answer"] = ""
        state["pending_action"] = "ask_question"
        state["waiting_for_user_input"] = True
        state["tool_result"] = ""
        state["last_tool_used"] = None
        return state

    return generate_question


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
