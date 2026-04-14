"""Node that appends the completed QA round to history."""

from app.graph.state import InterviewState


def save_round(state: InterviewState) -> InterviewState:
    history = list(state.get("history", []))
    question_key = state.get("current_question_key", "")

    already_saved = any(
        item.get("question_index") == state.get("current_question_index")
        and item.get("question_key") == question_key
        for item in history
    )
    if not already_saved and question_key and state.get("current_answer"):
        history.append(
            {
                "question_index": state.get("current_question_index", 0),
                "question_key": question_key,
                "question": state.get("current_question", ""),
                "answer": state.get("current_answer", ""),
                "score": state.get("current_score", 0),
                "verdict": state.get("current_verdict", "medium"),
                "feedback": state.get("current_feedback", ""),
                "missing_points": state.get("current_missing_points", []),
            }
        )
    state["history"] = history
    return state
