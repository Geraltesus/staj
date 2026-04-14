from app.graph.simple_nodes import _fallback_question


def test_fallback_question_is_not_plain_first_item_for_new_user():
    key, _question = _fallback_question({"user_id": 1, "chat_id": 1, "question_index": 0, "history": []})
    assert key != "what_is_goroutine"


def test_fallback_question_uses_answer_signal():
    key, _question = _fallback_question(
        {
            "user_id": 1,
            "chat_id": 1,
            "question_index": 1,
            "question_key": "what_is_goroutine",
            "question": "Что такое goroutine?",
            "answer": "Не уверен, как goroutine синхронизируются и где появляется race condition.",
            "feedback": "Нужно лучше раскрыть concurrency и синхронизацию.",
            "missing_points": ["synchronization", "race condition"],
            "history": [{"question_key": "what_is_goroutine"}],
        }
    )
    assert key in {"race_condition", "map_concurrency", "mutex_vs_channel", "what_is_channel"}
