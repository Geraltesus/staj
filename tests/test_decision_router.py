from app.graph.simple_nodes import route_decision


def test_route_tool_action():
    assert route_decision({"action": "generate_hint"}) == "run_tool"


def test_route_invalid_action_fallback():
    assert route_decision({"action": "dance"}) == "respond"
