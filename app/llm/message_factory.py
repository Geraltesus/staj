"""Factory for role-separated LangChain messages.

The code deliberately uses SystemMessage and HumanMessage instead of one large
string prompt. This makes the examples useful for learning LangGraph/LangChain
message design and keeps instructions clearer for small local models.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.prompts.decision_prompts import DECISION_HUMAN_TEMPLATE, DECISION_SYSTEM_PROMPT
from app.graph.prompts.evaluation_prompts import EVALUATION_HUMAN_TEMPLATE, EVALUATION_SYSTEM_PROMPT
from app.graph.prompts.question_prompts import QUESTION_HUMAN_TEMPLATE, QUESTION_SYSTEM_PROMPT
from app.graph.prompts.review_prompts import REVIEW_HUMAN_TEMPLATE, REVIEW_SYSTEM_PROMPT
from app.graph.state import InterviewState


def build_question_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    asked_keys = [item.get("question_key", "") for item in state.get("history", [])]
    human = QUESTION_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("current_level", "junior"),
        asked_keys=asked_keys,
        question_number=state.get("current_question_index", 0) + 1,
    )
    return [SystemMessage(content=QUESTION_SYSTEM_PROMPT), HumanMessage(content=human)]


def build_evaluation_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    human = EVALUATION_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("current_level", "junior"),
        question=state.get("current_question", ""),
        question_key=state.get("current_question_key", ""),
        answer=state.get("current_answer", ""),
    )
    return [SystemMessage(content=EVALUATION_SYSTEM_PROMPT), HumanMessage(content=human)]


def build_decision_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    human = DECISION_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("current_level", "junior"),
        question_index=state.get("current_question_index", 0),
        max_questions=state.get("max_questions", 3),
        question=state.get("current_question", ""),
        answer=state.get("current_answer", ""),
        score=state.get("current_score", 0),
        verdict=state.get("current_verdict", "medium"),
        feedback=state.get("current_feedback", ""),
        missing_points=state.get("current_missing_points", []),
        history=state.get("history", []),
    )
    return [SystemMessage(content=DECISION_SYSTEM_PROMPT), HumanMessage(content=human)]


def build_review_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    human = REVIEW_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("current_level", "junior"),
        history=state.get("history", []),
    )
    return [SystemMessage(content=REVIEW_SYSTEM_PROMPT), HumanMessage(content=human)]
