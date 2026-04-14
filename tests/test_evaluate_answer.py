from app.schemas.evaluation import EvaluationResult


def test_evaluation_score_is_clamped():
    result = EvaluationResult(score=99, verdict="strong", feedback="ok", missing_points=[])
    assert result.score == 10


def test_evaluation_verdict_fallback():
    result = EvaluationResult(score=5, verdict="strange", feedback="ok", missing_points=[])
    assert result.verdict == "medium"
