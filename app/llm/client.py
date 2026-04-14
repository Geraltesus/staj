"""Ollama client wrapper used by LangGraph nodes.

The wrapper centralizes retries, structured output parsing, and readable error
handling. The model is fixed by configuration and defaults to llama3.2:1b.
"""

import json
import time
from typing import Any, TypeVar

from langchain_ollama import ChatOllama
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMClientError(RuntimeError):
    """Raised when Ollama cannot produce a usable response."""


class OllamaLLMClient:
    """Small adapter around ChatOllama.

    It exposes one method for plain text calls and one method for Pydantic
    structured output. The structured method first asks LangChain for structured
    output, then falls back to JSON extraction from a normal response. This keeps
    the MVP more tolerant of local model quirks.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model_name = settings.ollama_model or "llama3.2:1b"
        self.client = ChatOllama(
            model=self.model_name,
            base_url=settings.ollama_base_url,
            temperature=0.2,
            timeout=settings.llm_timeout_seconds,
        )

    def invoke(self, messages: list[Any]) -> str:
        """Invoke Ollama and return text content, retrying transient failures."""

        last_error: Exception | None = None
        for attempt in range(self.settings.llm_retries + 1):
            try:
                response = self.client.invoke(messages)
                return str(response.content)
            except Exception as exc:  # pragma: no cover - depends on Docker/Ollama runtime
                last_error = exc
                logger.warning("Ollama text call failed on attempt %s: %s", attempt + 1, exc)
                time.sleep(1 + attempt)
        raise LLMClientError(f"Ollama call failed: {last_error}")

    def invoke_structured(self, messages: list[Any], schema: type[SchemaT]) -> SchemaT:
        """Invoke Ollama and parse the response as a Pydantic model.

        If native structured output fails, the method retries with a plain call
        and extracts the first JSON object from the response text.
        """

        last_error: Exception | None = None
        for attempt in range(self.settings.llm_retries + 1):
            try:
                structured_client = self.client.with_structured_output(schema)
                result = structured_client.invoke(messages)
                if isinstance(result, schema):
                    return result
                if isinstance(result, dict):
                    return schema.model_validate(result)
            except Exception as exc:
                last_error = exc
                logger.warning("Native structured call failed on attempt %s: %s", attempt + 1, exc)

            try:
                content = self.invoke(messages)
                payload = self._extract_json_object(content)
                return schema.model_validate(payload)
            except (json.JSONDecodeError, ValidationError, LLMClientError, ValueError) as exc:
                last_error = exc
                logger.warning("Structured parsing failed on attempt %s: %s", attempt + 1, exc)
                time.sleep(1 + attempt)

        raise LLMClientError(f"Structured Ollama call failed: {last_error}")

    @staticmethod
    def _extract_json_object(content: str) -> dict[str, Any]:
        """Extract the first JSON object from a model response."""

        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in LLM response")
        return json.loads(content[start : end + 1])
