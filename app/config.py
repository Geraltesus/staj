"""Application settings loaded from environment variables.

The project is intentionally Docker-first: defaults are useful inside Compose,
while `.env` lets the user tune MVP behavior without running Python locally.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API, graph, storage, and Ollama."""

    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    ollama_base_url: str = Field(default="http://ollama:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3.2:1b", alias="OLLAMA_MODEL")
    max_questions: int = Field(default=3, alias="MAX_QUESTIONS")
    default_topic: str = Field(default="golang_backend", alias="DEFAULT_TOPIC")
    default_level: str = Field(default="junior", alias="DEFAULT_LEVEL")
    sessions_dir: Path = Field(default=Path("/app/app/storage/sessions"), alias="SESSIONS_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    llm_retries: int = Field(default=2, alias="LLM_RETRIES")
    llm_timeout_seconds: int = Field(default=120, alias="LLM_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so dependencies share the same configuration."""

    return Settings()
