"""Node that starts a fresh interview."""

from app.graph.state import InterviewState


def init_interview(state: InterviewState) -> InterviewState:
    state["interview_started"] = True
    state["waiting_for_user_input"] = False
    state["pending_action"] = "ask_question"
    state["current_answer"] = ""
    state["error"] = ""
    return state
