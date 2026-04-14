"""Node that applies difficulty changes requested by the decision node."""

from app.graph.state import InterviewState
from app.utils.constants import LEVEL_ORDER


def adjust_difficulty(state: InterviewState) -> InterviewState:
    change = state.get("difficulty_change", "keep")
    current = state.get("current_level", "junior")
    try:
        index = LEVEL_ORDER.index(current)
    except ValueError:
        index = 0

    if change == "up":
        index = min(index + 1, len(LEVEL_ORDER) - 1)
    elif change == "down":
        index = max(index - 1, 0)

    state["current_level"] = LEVEL_ORDER[index]
    return state
