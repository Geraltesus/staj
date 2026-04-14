"""Answer evaluation node."""

from app.graph.state import InterviewState
from app.llm.client import LLMClientError, OllamaLLMClient
from app.llm.message_factory import build_evaluation_messages
from app.schemas.evaluation import EvaluationResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


def make_evaluate_answer_node(llm_client: OllamaLLMClient):
    def evaluate_answer(state: InterviewState) -> InterviewState:
        try:
            result = llm_client.invoke_structured(build_evaluation_messages(state), EvaluationResult)
        except LLMClientError as exc:
            logger.warning("Evaluation fallback used: %s", exc)
            result = _fallback_evaluation(state.get("current_answer", ""))

        state["current_score"] = result.score
        state["current_verdict"] = result.verdict
        state["current_feedback"] = result.feedback
        state["current_missing_points"] = result.missing_points
        return state

    return evaluate_answer


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
