"""Main orchestration use-case for interview interactions."""

from typing import Any

from app.config import Settings
from app.graph.state import InterviewState
from app.services.response_service import ResponseService
from app.services.session_service import SessionService
from app.utils.constants import DEFAULT_SAFE_REPLY, OLLAMA_UNAVAILABLE_REPLY
from app.utils.logger import get_logger

logger = get_logger(__name__)


class InterviewService:
    """Load session, run graph, save session, return text for an API client."""

    def __init__(self, settings: Settings, graph: Any, session_service: SessionService, response_service: ResponseService) -> None:
        self.settings = settings
        self.graph = graph
        self.session_service = session_service
        self.response_service = response_service

    async def handle_text(self, user_id: int, chat_id: int, text: str) -> str:
        """Backward-compatible helper that returns only the user-facing reply."""

        reply, _state = await self.handle_text_with_state(user_id, chat_id, text)
        return reply

    async def handle_text_with_state(self, user_id: int, chat_id: int, text: str) -> tuple[str, InterviewState]:
        """Process a command or answer and return both reply and persisted state."""

        normalized = text.strip()

        if normalized in {"/start", "/reset"}:
            state = self.session_service.reset_session(user_id, chat_id)
            state = await self._run_graph(state)
            self.session_service.save_session(user_id, state)
            return state.get("bot_reply", DEFAULT_SAFE_REPLY), state

        if normalized == "/finish":
            state = self.session_service.load_session(user_id, chat_id)
            state["pending_action"] = "finish"
            state = await self._run_graph(state)
            self.session_service.save_session(user_id, state)
            return state.get("bot_reply", DEFAULT_SAFE_REPLY), state

        if normalized == "/help":
            state = self.session_service.load_session(user_id, chat_id)
            return self.help_text(), state

        state = self.session_service.load_session(user_id, chat_id)
        if not state.get("interview_started"):
            state = await self._run_graph(state)
            self.session_service.save_session(user_id, state)
            reply = "Интервью ещё не было начато, поэтому я стартовал новое.\n\n" + state.get("bot_reply", "")
            return reply, state

        state["current_answer"] = normalized
        state = await self._run_graph(state)
        self.session_service.save_session(user_id, state)
        return state.get("bot_reply", DEFAULT_SAFE_REPLY), state

    @staticmethod
    def help_text() -> str:
        return (
            "Я HTTP API-наставник для mock interview.\n\n"
            "Endpoints:\n"
            "POST /interviews/start - начать интервью заново\n"
            "POST /interviews/answer - отправить ответ кандидата\n"
            "POST /interviews/finish - завершить интервью и получить feedback\n"
            "POST /interviews/reset - сбросить сессию\n"
            "GET /docs - открыть Swagger UI"
        )

    async def _run_graph(self, state: InterviewState) -> InterviewState:
        try:
            return await self.graph.ainvoke(state)
        except Exception as exc:
            logger.exception("Graph execution failed: %s", exc)
            state["error"] = str(exc)
            state["bot_reply"] = OLLAMA_UNAVAILABLE_REPLY if "Ollama" in str(exc) else DEFAULT_SAFE_REPLY
            return state
