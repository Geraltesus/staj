"""Small dependency factory module.

Keeping object construction here makes routes and services easy to read and
keeps infrastructure choices out of business use-cases.
"""

from app.config import Settings, get_settings
from app.graph.builder import build_interview_graph
from app.llm.client import OllamaLLMClient
from app.services.interview_service import InterviewService
from app.storage.sessions import SessionRepository


def build_interview_service(settings: Settings | None = None) -> InterviewService:
    """Assemble the application service used by API routes."""

    settings = settings or get_settings()
    llm_client = OllamaLLMClient(settings=settings)
    graph = build_interview_graph(llm_client=llm_client)
    sessions = SessionRepository(settings=settings)
    return InterviewService(
        settings=settings,
        graph=graph,
        sessions=sessions,
    )
