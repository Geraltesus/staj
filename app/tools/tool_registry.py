"""Registry for local interview tools.

No external MCP SDK is used here. The registry is intentionally just a small
mapping of tool names to Python callables so students can see the mechanics.
"""

from collections.abc import Callable

from app.tools.hint_tool import generate_hint
from app.tools.reference_tool import get_reference_answer


class ToolRegistry:
    """Lookup and execute local tools by name."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[[str, str, str], str]] = {
            "generate_hint": generate_hint,
            "get_reference_answer": get_reference_answer,
        }

    def run(self, tool_name: str, topic: str, level: str, question_key: str) -> str:
        tool = self._tools.get(tool_name)
        if tool is None:
            return "Инструмент не найден. Попробуем продолжить интервью без него."
        return tool(topic, level, question_key)

    @property
    def names(self) -> list[str]:
        return sorted(self._tools.keys())
