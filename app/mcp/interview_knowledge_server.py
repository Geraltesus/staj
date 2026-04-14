"""MCP server exposing the local interview knowledge base."""

from mcp.server.fastmcp import FastMCP

from app.tools.local_tools import generate_hint as read_hint
from app.tools.local_tools import get_reference_answer as read_reference_answer

mcp = FastMCP("interview-knowledge")


@mcp.tool()
def generate_hint(topic: str, level: str, question_key: str) -> str:
    """Return a hint for a known interview question."""

    return read_hint(topic, level, question_key)


@mcp.tool()
def get_reference_answer(topic: str, level: str, question_key: str) -> str:
    """Return a reference answer for a known interview question."""

    return read_reference_answer(topic, level, question_key)


def main() -> None:
    """Run the MCP server over stdio."""

    mcp.run()


if __name__ == "__main__":
    main()
