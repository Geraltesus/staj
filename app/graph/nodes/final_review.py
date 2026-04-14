"""Final review node."""

from app.graph.state import InterviewState
from app.llm.client import LLMClientError, OllamaLLMClient
from app.llm.message_factory import build_review_messages
from app.schemas.review import FinalReviewResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


def make_final_review_node(llm_client: OllamaLLMClient):
    def final_review(state: InterviewState) -> InterviewState:
        try:
            result = llm_client.invoke_structured(build_review_messages(state), FinalReviewResult)
        except LLMClientError as exc:
            logger.warning("Final review fallback used: %s", exc)
            result = _fallback_review(state)

        state["final_summary"] = result.summary
        state["strong_sides"] = result.strong_sides
        state["weak_sides"] = result.weak_sides
        state["improvement_plan"] = result.improvement_plan
        state["waiting_for_user_input"] = False
        return state

    return final_review


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
