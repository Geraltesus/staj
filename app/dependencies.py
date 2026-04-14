"""Small dependency factory module.

Keeping object construction here makes routes and services easy to read and
keeps infrastructure choices out of business use-cases.
"""

from app.config import Settings, get_settings
from app.graph.builder import build_interview_graph
from app.llm.client import OllamaLLMClient
from app.services.interview_service import InterviewService
from app.services.response_service import ResponseService
from app.services.session_service import SessionService
from app.storage.session_repository import SessionRepository
from app.tools.tool_registry import ToolRegistry


def build_interview_service(settings: Settings | None = None) -> InterviewService:
    """Assemble the application service used by API routes."""

    settings = settings or get_settings()
    llm_client = OllamaLLMClient(settings=settings)
    tool_registry = ToolRegistry()
    graph = build_interview_graph(llm_client=llm_client, tool_registry=tool_registry)
    session_repository = SessionRepository(settings=settings)
    session_service = SessionService(repository=session_repository)
    response_service = ResponseService()
    return InterviewService(
        settings=settings,
        graph=graph,
        session_service=session_service,
        response_service=response_service,
    )
