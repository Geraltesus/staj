"""Repository for JSON session files: one API user per file."""

from pathlib import Path

from app.config import Settings
from app.graph.state import InterviewState, create_default_state
from app.storage.json_store import JsonStore


class SessionRepository:
    """Persist and restore interview state from JSON files."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.sessions_dir = Path(settings.sessions_dir)
        self.store = JsonStore()
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def load_session(self, user_id: int, chat_id: int | None = None) -> InterviewState:
        path = self._path_for_user(user_id)
        default = create_default_state(
            user_id=user_id,
            chat_id=chat_id or user_id,
            topic=self.settings.default_topic,
            level=self.settings.default_level,
            max_questions=self.settings.max_questions,
        )
        data = self.store.read(path, default=default)
        merged = {**default, **data}
        if "telegram_user_id" in merged:
            merged["user_id"] = merged.pop("telegram_user_id")
        if chat_id is not None:
            merged["chat_id"] = chat_id
        return merged

    def save_session(self, user_id: int, state: InterviewState) -> None:
        clean_state = dict(state)
        clean_state.pop("telegram_user_id", None)
        self.store.write(self._path_for_user(user_id), clean_state)

    def reset_session(self, user_id: int, chat_id: int | None = None) -> InterviewState:
        state = create_default_state(
            user_id=user_id,
            chat_id=chat_id or user_id,
            topic=self.settings.default_topic,
            level=self.settings.default_level,
            max_questions=self.settings.max_questions,
        )
        self.save_session(user_id, state)
        return state

    def _path_for_user(self, user_id: int) -> Path:
        return self.sessions_dir / f"{user_id}.json"
