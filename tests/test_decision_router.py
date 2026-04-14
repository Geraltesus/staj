from app.graph.routers.decision_router import route_by_decision


def test_route_valid_action():
    assert route_by_decision({"pending_action": "generate_hint"}) == "generate_hint"


def test_route_invalid_action_fallback():
    assert route_by_decision({"pending_action": "dance"}) == "clarify"
