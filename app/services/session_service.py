"""Application service for session lifecycle operations."""

from app.graph.state import InterviewState
from app.storage.session_repository import SessionRepository


class SessionService:
    """Thin service wrapper over SessionRepository."""

    def __init__(self, repository: SessionRepository) -> None:
        self.repository = repository

    def load_session(self, user_id: int, chat_id: int) -> InterviewState:
        return self.repository.load_session(user_id=user_id, chat_id=chat_id)

    def save_session(self, user_id: int, state: InterviewState) -> None:
        self.repository.save_session(user_id=user_id, state=state)

    def reset_session(self, user_id: int, chat_id: int) -> InterviewState:
        return self.repository.reset_session(user_id=user_id, chat_id=chat_id)
