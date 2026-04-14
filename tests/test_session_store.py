from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from app.storage.sessions import SessionRepository


class DummySettings(BaseSettings):
    default_topic: str = "golang_backend"
    default_level: str = "junior"
    max_questions: int = 3
    sessions_dir: Path = Field(default_factory=Path)


def test_save_and_load_session(tmp_path):
    settings = DummySettings(sessions_dir=tmp_path)
    repo = SessionRepository(settings)  # type: ignore[arg-type]
    state = repo.reset_session(123, 456)
    state["question"] = "What is goroutine?"
    repo.save_session(123, state)

    loaded = repo.load_session(123, 456)
    assert loaded["user_id"] == 123
    assert loaded["chat_id"] == 456
    assert loaded["question"] == "What is goroutine?"
