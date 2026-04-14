"""LangGraph builder for the interview workflow."""

from langgraph.graph import END, StateGraph

from app.graph.nodes.adjust_difficulty import adjust_difficulty
from app.graph.nodes.agent_decision import make_agent_decision_node
from app.graph.nodes.evaluate_answer import make_evaluate_answer_node
from app.graph.nodes.final_review import make_final_review_node
from app.graph.nodes.format_output import format_output
from app.graph.nodes.generate_question import make_generate_question_node
from app.graph.nodes.init_interview import init_interview
from app.graph.nodes.save_round import save_round
from app.graph.routers.decision_router import route_by_decision
from app.graph.state import InterviewState
from app.llm.client import OllamaLLMClient
from app.tools.tool_registry import ToolRegistry


def build_interview_graph(llm_client: OllamaLLMClient, tool_registry: ToolRegistry):
    """Build and compile the StateGraph used by InterviewService."""

    graph = StateGraph(InterviewState)
    graph.add_node("init_interview", init_interview)
    graph.add_node("generate_question", make_generate_question_node(llm_client))
    graph.add_node("evaluate_answer", make_evaluate_answer_node(llm_client))
    graph.add_node("agent_decision", make_agent_decision_node(llm_client))
    graph.add_node("adjust_difficulty", adjust_difficulty)
    graph.add_node("save_round", save_round)
    graph.add_node("final_review", make_final_review_node(llm_client))
    graph.add_node("format_output", format_output)
    graph.add_node("generate_hint", _make_tool_node(tool_registry, "generate_hint"))
    graph.add_node("get_reference_answer", _make_tool_node(tool_registry, "get_reference_answer"))

    graph.set_conditional_entry_point(
        _entry_route,
        {
            "init_interview": "init_interview",
            "evaluate_answer": "evaluate_answer",
            "save_round": "save_round",
        },
    )
    graph.add_edge("init_interview", "generate_question")
    graph.add_edge("generate_question", "format_output")
    graph.add_edge("evaluate_answer", "agent_decision")
    graph.add_conditional_edges(
        "agent_decision",
        route_by_decision,
        {
            "ask_question": "adjust_difficulty",
            "clarify": "format_output",
            "generate_hint": "generate_hint",
            "get_reference_answer": "get_reference_answer",
            "finish": "save_round",
        },
    )
    graph.add_edge("adjust_difficulty", "save_round")
    graph.add_conditional_edges(
        "save_round",
        lambda state: "final_review" if state.get("pending_action") == "finish" else "generate_question",
        {"final_review": "final_review", "generate_question": "generate_question"},
    )
    graph.add_edge("generate_hint", "format_output")
    graph.add_edge("get_reference_answer", "format_output")
    graph.add_edge("final_review", "format_output")
    graph.add_edge("format_output", END)
    return graph.compile()


def _entry_route(state: InterviewState) -> str:
    if not state.get("interview_started"):
        return "init_interview"
    if state.get("pending_action") == "finish":
        return "save_round"
    return "evaluate_answer"


def _make_tool_node(tool_registry: ToolRegistry, tool_name: str):
    def tool_node(state: InterviewState) -> InterviewState:
        state["tool_result"] = tool_registry.run(
            tool_name=tool_name,
            topic=state.get("topic", "golang_backend"),
            level=state.get("current_level", "junior"),
            question_key=state.get("current_question_key", ""),
        )
        state["last_tool_used"] = tool_name
        state["pending_action"] = tool_name
        return state

    return tool_node
