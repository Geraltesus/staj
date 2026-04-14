"""Node that converts state into a API-ready reply."""

from app.graph.state import InterviewState
from app.services.response_service import ResponseService
from app.utils.constants import DEFAULT_SAFE_REPLY


def format_output(state: InterviewState) -> InterviewState:
    response_service = ResponseService()
    action = state.get("pending_action", "ask_question")

    if state.get("final_summary") and action == "finish":
        reply = response_service.final_review(state)
        state["waiting_for_user_input"] = False
    elif action == "clarify":
        reply = response_service.clarify(state)
        state["waiting_for_user_input"] = True
    elif action == "generate_hint":
        reply = response_service.hint(state)
        state["waiting_for_user_input"] = True
    elif action == "get_reference_answer":
        reply = response_service.reference_answer(state)
        state["waiting_for_user_input"] = True
    elif state.get("current_question"):
        reply = response_service.question(state)
        state["waiting_for_user_input"] = True
    else:
        reply = DEFAULT_SAFE_REPLY
        state["waiting_for_user_input"] = True

    state["bot_reply"] = reply
    return state
