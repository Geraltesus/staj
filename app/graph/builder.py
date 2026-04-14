"""LangGraph builder for the simplified interview workflow."""

from langgraph.graph import END, StateGraph

from app.graph.simple_nodes import (
    make_ask_question_node,
    make_decide_next_node,
    make_evaluate_answer_node,
    make_final_review_node,
    respond,
    route_decision,
    route_input,
    run_tool,
)
from app.graph.state import InterviewState
from app.llm.client import OllamaLLMClient


def build_interview_graph(llm_client: OllamaLLMClient):
    """Build a compact graph whose nodes are semantic agent actions."""

    graph = StateGraph(InterviewState)
    graph.add_node("ask_question", make_ask_question_node(llm_client))
    graph.add_node("evaluate_answer", make_evaluate_answer_node(llm_client))
    graph.add_node("decide_next", make_decide_next_node(llm_client))
    graph.add_node("run_tool", run_tool)
    graph.add_node("final_review", make_final_review_node(llm_client))
    graph.add_node("respond", respond)

    graph.set_conditional_entry_point(
        route_input,
        {
            "ask_question": "ask_question",
            "evaluate_answer": "evaluate_answer",
            "final_review": "final_review",
        },
    )
    graph.add_edge("ask_question", "respond")
    graph.add_edge("evaluate_answer", "decide_next")
    graph.add_conditional_edges(
        "decide_next",
        route_decision,
        {
            "ask_question": "ask_question",
            "run_tool": "run_tool",
            "final_review": "final_review",
            "respond": "respond",
        },
    )
    graph.add_edge("run_tool", "respond")
    graph.add_edge("final_review", "respond")
    graph.add_edge("respond", END)
    return graph.compile()
