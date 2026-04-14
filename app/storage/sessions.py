"""JSON session storage for interview state."""

import json
from pathlib import Path

from app.config import Settings
from app.graph.state import InterviewState, create_default_state
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SessionRepository:
    """Persist and restore one interview state per API user."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.sessions_dir = Path(settings.sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def load_session(self, user_id: int, chat_id: int | None = None) -> InterviewState:
        default = create_default_state(
            user_id=user_id,
            chat_id=chat_id or user_id,
            topic=self.settings.default_topic,
            level=self.settings.default_level,
            max_questions=self.settings.max_questions,
        )
        data = self._read(self._path_for_user(user_id), default={})
        state = _migrate_state({**default, **data})
        if chat_id is not None:
            state["chat_id"] = chat_id
        return state

    def save_session(self, user_id: int, state: InterviewState) -> None:
        self._write(self._path_for_user(user_id), dict(state))

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

    @staticmethod
    def _read(path: Path, default: dict) -> dict:
        try:
            if not path.exists():
                return default
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to read session file %s: %s", path, exc)
            return default

    @staticmethod
    def _write(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)


def _migrate_state(state: dict) -> InterviewState:
    rename_map = {
        "current_level": "level",
        "current_question_index": "question_index",
        "current_question": "question",
        "current_question_key": "question_key",
        "current_answer": "answer",
        "current_score": "score",
        "current_verdict": "verdict",
        "current_feedback": "feedback",
        "current_missing_points": "missing_points",
        "pending_action": "action",
        "final_summary": "final_summary",
    }
    for old, new in rename_map.items():
        if old in state:
            state[new] = state[old]
        state.pop(old, None)

    for unused in ("telegram_user_id", "retry_count", "last_tool_used", "waiting_for_user_input", "decision_reason", "difficulty_change", "error"):
        state.pop(unused, None)
    return state
