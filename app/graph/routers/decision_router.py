"""LangGraph router for the action selected by the decision node."""

from app.graph.state import InterviewState
from app.utils.validators import normalize_action


def route_by_decision(state: InterviewState) -> str:
    """Return the next graph edge label from state['pending_action']."""

    return normalize_action(state.get("pending_action", "clarify"))
