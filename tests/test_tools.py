from app.tools.hint_tool import FALLBACK_HINT, generate_hint
from app.tools.reference_tool import FALLBACK_REFERENCE, get_reference_answer


def test_reference_answer_from_json():
    answer = get_reference_answer("golang_backend", "junior", "what_is_goroutine")
    assert "Goroutine" in answer


def test_reference_answer_fallback():
    answer = get_reference_answer("unknown", "junior", "missing")
    assert answer == FALLBACK_REFERENCE


def test_hint_from_json():
    hint = generate_hint("golang_backend", "junior", "what_is_channel")
    assert "goroutine" in hint.lower()


def test_hint_fallback():
    hint = generate_hint("unknown", "junior", "missing")
    assert hint == FALLBACK_HINT
