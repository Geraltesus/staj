"""Small MCP stdio client for the interview knowledge server."""

import os
import sys

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from app.graph.state import InterviewState


async def call_interview_tool(action: str, state: InterviewState) -> str:
    """Call the local interview knowledge MCP server and return plain text."""

    arguments = {
        "topic": state.get("topic", "golang_backend"),
        "level": state.get("level", "junior"),
        "question_key": state.get("question_key", ""),
    }
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp.interview_knowledge_server"],
        env=_subprocess_env(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(action, arguments)
            return _text_from_result(result)


def _subprocess_env() -> dict[str, str]:
    env = dict(os.environ)
    pythonpath = env.get("PYTHONPATH")
    cwd = os.getcwd()
    env["PYTHONPATH"] = cwd if not pythonpath else os.pathsep.join([cwd, pythonpath])
    return env


def _text_from_result(result: types.CallToolResult) -> str:
    if result.isError:
        messages = [content.text for content in result.content if isinstance(content, types.TextContent)]
        raise RuntimeError("; ".join(messages) or "MCP tool execution failed")

    text_parts = [content.text for content in result.content if isinstance(content, types.TextContent)]
    if text_parts:
        return "\n".join(text_parts)

    structured = getattr(result, "structuredContent", None)
    if structured:
        return str(structured)
    return ""
