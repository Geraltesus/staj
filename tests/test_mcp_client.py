import asyncio

from app.tools.mcp_client import call_interview_tool


def test_mcp_reference_answer_tool():
    state = {
        "topic": "golang_backend",
        "level": "junior",
        "question_key": "what_is_goroutine",
    }

    answer = asyncio.run(call_interview_tool("get_reference_answer", state))

    assert "Goroutine" in answer
