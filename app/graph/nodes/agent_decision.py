"""Agent decision node that lets the LLM choose the next route."""

from app.graph.state import InterviewState
from app.llm.client import LLMClientError, OllamaLLMClient
from app.llm.message_factory import build_decision_messages
from app.schemas.decision import DecisionResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


def make_agent_decision_node(llm_client: OllamaLLMClient):
    def agent_decision(state: InterviewState) -> InterviewState:
        try:
            result = llm_client.invoke_structured(build_decision_messages(state), DecisionResult)
        except LLMClientError as exc:
            logger.warning("Decision fallback used: %s", exc)
            result = _fallback_decision(state)

        if int(state.get("current_question_index", 0)) >= int(state.get("max_questions", 3)):
            result.action = "finish"
            result.difficulty_change = "keep"

        state["pending_action"] = result.action
        state["difficulty_change"] = result.difficulty_change
        state["decision_reason"] = result.reason
        return state

    return agent_decision


def _fallback_decision(state: InterviewState) -> DecisionResult:
    if int(state.get("current_question_index", 0)) >= int(state.get("max_questions", 3)):
        return DecisionResult(action="finish", difficulty_change="keep", reason="Reached max questions")
    if len(state.get("current_answer", "").strip()) < 30:
        return DecisionResult(action="clarify", difficulty_change="keep", reason="Answer is too short")
    return DecisionResult(action="ask_question", difficulty_change="keep", reason="Safe fallback continues interview")
