"""Safe JSON file helper used by repositories and local tools."""

import json
from pathlib import Path
from typing import Any

from app.utils.logger import get_logger

logger = get_logger(__name__)


class JsonStore:
    """Tiny JSON store with defensive reads and atomic-ish writes."""

    def read(self, path: Path, default: Any) -> Any:
        try:
            if not path.exists():
                return default
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to read JSON file %s: %s", path, exc)
            return default

    def write(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)
