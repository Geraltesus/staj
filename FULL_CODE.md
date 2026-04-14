# Full Project Code

## File Tree

```text
./
  .dockerignore
  .env
  .env.example
  .gitignore
  app/__init__.py
  app/api/__init__.py
  app/api/routes.py
  app/config.py
  app/dependencies.py
  app/graph/__init__.py
  app/graph/builder.py
  app/graph/nodes/__init__.py
  app/graph/nodes/adjust_difficulty.py
  app/graph/nodes/agent_decision.py
  app/graph/nodes/evaluate_answer.py
  app/graph/nodes/final_review.py
  app/graph/nodes/format_output.py
  app/graph/nodes/generate_question.py
  app/graph/nodes/init_interview.py
  app/graph/nodes/save_round.py
  app/graph/prompts/__init__.py
  app/graph/prompts/decision_prompts.py
  app/graph/prompts/evaluation_prompts.py
  app/graph/prompts/question_prompts.py
  app/graph/prompts/review_prompts.py
  app/graph/routers/__init__.py
  app/graph/routers/decision_router.py
  app/graph/state.py
  app/llm/__init__.py
  app/llm/client.py
  app/llm/message_factory.py
  app/main.py
  app/schemas/__init__.py
  app/schemas/api.py
  app/schemas/decision.py
  app/schemas/evaluation.py
  app/schemas/review.py
  app/services/__init__.py
  app/services/interview_service.py
  app/services/response_service.py
  app/services/session_service.py
  app/storage/__init__.py
  app/storage/json_store.py
  app/storage/session_repository.py
  app/storage/sessions/.gitkeep
  app/tools/__init__.py
  app/tools/data/hints.json
  app/tools/data/reference_answers.json
  app/tools/hint_tool.py
  app/tools/reference_tool.py
  app/tools/tool_registry.py
  app/utils/__init__.py
  app/utils/constants.py
  app/utils/logger.py
  app/utils/validators.py
  app/web/__init__.py
  app/web/chat_page.py
  docker/app/docker-entrypoint.sh
  docker/app/Dockerfile
  docker/ollama/init-model.sh
  docker-compose.yml
  FULL_CODE.md
  graph.mmd
  graph.png
  README.md
  requirements.txt
  scripts/render_graph_png.py
  tests/test_decision_router.py
  tests/test_evaluate_answer.py
  tests/test_session_store.py
  tests/test_tools.py
```

Binary assets such as graph.png are listed in the tree but not embedded as code blocks.

## .dockerignore
```gitignore
.git
.pytest_cache
__pycache__
*.pyc
.env
app/storage/sessions/*.json
.venv
venv
.idea
.vscode

```

## .env
```dotenv
APP_HOST=0.0.0.0
APP_PORT=8000
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:1b
MAX_QUESTIONS=3
DEFAULT_TOPIC=golang_backend
DEFAULT_LEVEL=junior
SESSIONS_DIR=/app/app/storage/sessions
LOG_LEVEL=INFO

```

## .env.example
```dotenv
APP_HOST=0.0.0.0
APP_PORT=8000
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:1b
MAX_QUESTIONS=3
DEFAULT_TOPIC=golang_backend
DEFAULT_LEVEL=junior
SESSIONS_DIR=/app/app/storage/sessions
LOG_LEVEL=INFO

```

## .gitignore
```gitignore
.env
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.venv/
venv/
app/storage/sessions/*.json
!app/storage/sessions/.gitkeep
.DS_Store

```

## app/__init__.py
```py


```

## app/api/__init__.py
```py


```

## app/api/routes.py
```py
"""FastAPI routes for the interview mentor.

This replaces the Telegram transport with a local HTTP interface that is easier
for Docker-only learning: use curl, Postman, Swagger UI, or connect a frontend.
"""

from fastapi import APIRouter, Depends

from app.dependencies import build_interview_service
from app.schemas.api import AnswerRequest, HealthResponse, InterviewResponse, StartInterviewRequest
from app.services.interview_service import InterviewService

router = APIRouter()


def get_interview_service() -> InterviewService:
    """FastAPI dependency wrapper for the service factory."""

    return build_interview_service()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", transport="http")


@router.post("/interviews/start", response_model=InterviewResponse)
async def start_interview(
    request: StartInterviewRequest,
    service: InterviewService = Depends(get_interview_service),
) -> InterviewResponse:
    chat_id = request.chat_id or request.user_id
    reply, state = await service.handle_text_with_state(request.user_id, chat_id, "/start")
    return InterviewResponse(user_id=request.user_id, reply=reply, state=dict(state))


@router.post("/interviews/answer", response_model=InterviewResponse)
async def answer_question(
    request: AnswerRequest,
    service: InterviewService = Depends(get_interview_service),
) -> InterviewResponse:
    chat_id = request.chat_id or request.user_id
    reply, state = await service.handle_text_with_state(request.user_id, chat_id, request.text)
    return InterviewResponse(user_id=request.user_id, reply=reply, state=dict(state))


@router.post("/interviews/finish", response_model=InterviewResponse)
async def finish_interview(
    request: StartInterviewRequest,
    service: InterviewService = Depends(get_interview_service),
) -> InterviewResponse:
    chat_id = request.chat_id or request.user_id
    reply, state = await service.handle_text_with_state(request.user_id, chat_id, "/finish")
    return InterviewResponse(user_id=request.user_id, reply=reply, state=dict(state))


@router.post("/interviews/reset", response_model=InterviewResponse)
async def reset_interview(
    request: StartInterviewRequest,
    service: InterviewService = Depends(get_interview_service),
) -> InterviewResponse:
    chat_id = request.chat_id or request.user_id
    reply, state = await service.handle_text_with_state(request.user_id, chat_id, "/reset")
    return InterviewResponse(user_id=request.user_id, reply=reply, state=dict(state))


@router.get("/interviews/{user_id}/session", response_model=InterviewResponse)
async def get_session(
    user_id: int,
    service: InterviewService = Depends(get_interview_service),
) -> InterviewResponse:
    state = service.session_service.load_session(user_id, user_id)
    return InterviewResponse(user_id=user_id, reply=state.get("bot_reply", ""), state=dict(state))

```

## app/config.py
```py
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

```

## app/dependencies.py
```py
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

```

## app/graph/__init__.py
```py


```

## app/graph/builder.py
```py
"""LangGraph builder for the interview workflow."""

from langgraph.graph import END, StateGraph

from app.graph.nodes.adjust_difficulty import adjust_difficulty
from app.graph.nodes.agent_decision import make_agent_decision_node
from app.graph.nodes.evaluate_answer import make_evaluate_answer_node
from app.graph.nodes.final_review import make_final_review_node
from app.graph.nodes.format_output import format_output
from app.graph.nodes.generate_question import make_generate_question_node
from app.graph.nodes.init_interview import init_interview
from app.graph.nodes.save_round import save_round
from app.graph.routers.decision_router import route_by_decision
from app.graph.state import InterviewState
from app.llm.client import OllamaLLMClient
from app.tools.tool_registry import ToolRegistry


def build_interview_graph(llm_client: OllamaLLMClient, tool_registry: ToolRegistry):
    """Build and compile the StateGraph used by InterviewService."""

    graph = StateGraph(InterviewState)
    graph.add_node("init_interview", init_interview)
    graph.add_node("generate_question", make_generate_question_node(llm_client))
    graph.add_node("evaluate_answer", make_evaluate_answer_node(llm_client))
    graph.add_node("agent_decision", make_agent_decision_node(llm_client))
    graph.add_node("adjust_difficulty", adjust_difficulty)
    graph.add_node("save_round", save_round)
    graph.add_node("final_review", make_final_review_node(llm_client))
    graph.add_node("format_output", format_output)
    graph.add_node("generate_hint", _make_tool_node(tool_registry, "generate_hint"))
    graph.add_node("get_reference_answer", _make_tool_node(tool_registry, "get_reference_answer"))

    graph.set_conditional_entry_point(
        _entry_route,
        {
            "init_interview": "init_interview",
            "evaluate_answer": "evaluate_answer",
            "save_round": "save_round",
        },
    )
    graph.add_edge("init_interview", "generate_question")
    graph.add_edge("generate_question", "format_output")
    graph.add_edge("evaluate_answer", "agent_decision")
    graph.add_conditional_edges(
        "agent_decision",
        route_by_decision,
        {
            "ask_question": "adjust_difficulty",
            "clarify": "format_output",
            "generate_hint": "generate_hint",
            "get_reference_answer": "get_reference_answer",
            "finish": "save_round",
        },
    )
    graph.add_edge("adjust_difficulty", "save_round")
    graph.add_conditional_edges(
        "save_round",
        lambda state: "final_review" if state.get("pending_action") == "finish" else "generate_question",
        {"final_review": "final_review", "generate_question": "generate_question"},
    )
    graph.add_edge("generate_hint", "format_output")
    graph.add_edge("get_reference_answer", "format_output")
    graph.add_edge("final_review", "format_output")
    graph.add_edge("format_output", END)
    return graph.compile()


def _entry_route(state: InterviewState) -> str:
    if not state.get("interview_started"):
        return "init_interview"
    if state.get("pending_action") == "finish":
        return "save_round"
    return "evaluate_answer"


def _make_tool_node(tool_registry: ToolRegistry, tool_name: str):
    def tool_node(state: InterviewState) -> InterviewState:
        state["tool_result"] = tool_registry.run(
            tool_name=tool_name,
            topic=state.get("topic", "golang_backend"),
            level=state.get("current_level", "junior"),
            question_key=state.get("current_question_key", ""),
        )
        state["last_tool_used"] = tool_name
        state["pending_action"] = tool_name
        return state

    return tool_node

```

## app/graph/nodes/__init__.py
```py


```

## app/graph/nodes/adjust_difficulty.py
```py
"""Node that applies difficulty changes requested by the decision node."""

from app.graph.state import InterviewState
from app.utils.constants import LEVEL_ORDER


def adjust_difficulty(state: InterviewState) -> InterviewState:
    change = state.get("difficulty_change", "keep")
    current = state.get("current_level", "junior")
    try:
        index = LEVEL_ORDER.index(current)
    except ValueError:
        index = 0

    if change == "up":
        index = min(index + 1, len(LEVEL_ORDER) - 1)
    elif change == "down":
        index = max(index - 1, 0)

    state["current_level"] = LEVEL_ORDER[index]
    return state

```

## app/graph/nodes/agent_decision.py
```py
"""Agent decision node that lets the LLM choose the next route."""

from app.graph.state import InterviewState
from app.llm.client import LLMClientError, OllamaLLMClient
from app.llm.message_factory import build_decision_messages
from app.schemas.decision import DecisionResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


def make_agent_decision_node(llm_client: OllamaLLMClient):
    def agent_decision(state: InterviewState) -> InterviewState:
        try:
            result = llm_client.invoke_structured(build_decision_messages(state), DecisionResult)
        except LLMClientError as exc:
            logger.warning("Decision fallback used: %s", exc)
            result = _fallback_decision(state)

        if int(state.get("current_question_index", 0)) >= int(state.get("max_questions", 3)):
            result.action = "finish"
            result.difficulty_change = "keep"

        state["pending_action"] = result.action
        state["difficulty_change"] = result.difficulty_change
        state["decision_reason"] = result.reason
        return state

    return agent_decision


def _fallback_decision(state: InterviewState) -> DecisionResult:
    if int(state.get("current_question_index", 0)) >= int(state.get("max_questions", 3)):
        return DecisionResult(action="finish", difficulty_change="keep", reason="Reached max questions")
    if len(state.get("current_answer", "").strip()) < 30:
        return DecisionResult(action="clarify", difficulty_change="keep", reason="Answer is too short")
    return DecisionResult(action="ask_question", difficulty_change="keep", reason="Safe fallback continues interview")

```

## app/graph/nodes/evaluate_answer.py
```py
"""Answer evaluation node."""

from app.graph.state import InterviewState
from app.llm.client import LLMClientError, OllamaLLMClient
from app.llm.message_factory import build_evaluation_messages
from app.schemas.evaluation import EvaluationResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


def make_evaluate_answer_node(llm_client: OllamaLLMClient):
    def evaluate_answer(state: InterviewState) -> InterviewState:
        try:
            result = llm_client.invoke_structured(build_evaluation_messages(state), EvaluationResult)
        except LLMClientError as exc:
            logger.warning("Evaluation fallback used: %s", exc)
            result = _fallback_evaluation(state.get("current_answer", ""))

        state["current_score"] = result.score
        state["current_verdict"] = result.verdict
        state["current_feedback"] = result.feedback
        state["current_missing_points"] = result.missing_points
        return state

    return evaluate_answer


def _fallback_evaluation(answer: str) -> EvaluationResult:
    if len(answer.strip()) < 30:
        return EvaluationResult(
            score=3,
            verdict="weak",
            feedback="Ответ выглядит слишком коротким. Добавьте определение, назначение и пример.",
            missing_points=["definition", "practical example"],
        )
    return EvaluationResult(
        score=6,
        verdict="medium",
        feedback="Ответ принят, но модель оценки временно недоступна. Продолжим осторожно.",
        missing_points=[],
    )

```

## app/graph/nodes/final_review.py
```py
"""Final review node."""

from app.graph.state import InterviewState
from app.llm.client import LLMClientError, OllamaLLMClient
from app.llm.message_factory import build_review_messages
from app.schemas.review import FinalReviewResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


def make_final_review_node(llm_client: OllamaLLMClient):
    def final_review(state: InterviewState) -> InterviewState:
        try:
            result = llm_client.invoke_structured(build_review_messages(state), FinalReviewResult)
        except LLMClientError as exc:
            logger.warning("Final review fallback used: %s", exc)
            result = _fallback_review(state)

        state["final_summary"] = result.summary
        state["strong_sides"] = result.strong_sides
        state["weak_sides"] = result.weak_sides
        state["improvement_plan"] = result.improvement_plan
        state["waiting_for_user_input"] = False
        return state

    return final_review


def _fallback_review(state: InterviewState) -> FinalReviewResult:
    history = state.get("history", [])
    avg_score = 0
    if history:
        avg_score = round(sum(int(item.get("score", 0)) for item in history) / len(history))
    return FinalReviewResult(
        summary=f"Интервью завершено. Средняя оценка: {avg_score}/10. Продолжайте тренировать структурные ответы.",
        strong_sides=["Вы прошли все вопросы MVP-интервью"],
        weak_sides=["Некоторые ответы стоит делать более конкретными"],
        improvement_plan=["Отвечайте по схеме: определение, зачем нужно, пример", "Повторите goroutine, channels и синхронизацию"],
    )

```

## app/graph/nodes/format_output.py
```py
"""Node that converts state into a API-ready reply."""

from app.graph.state import InterviewState
from app.services.response_service import ResponseService
from app.utils.constants import DEFAULT_SAFE_REPLY


def format_output(state: InterviewState) -> InterviewState:
    response_service = ResponseService()
    action = state.get("pending_action", "ask_question")

    if state.get("final_summary") and action == "finish":
        reply = response_service.final_review(state)
        state["waiting_for_user_input"] = False
    elif action == "clarify":
        reply = response_service.clarify(state)
        state["waiting_for_user_input"] = True
    elif action == "generate_hint":
        reply = response_service.hint(state)
        state["waiting_for_user_input"] = True
    elif action == "get_reference_answer":
        reply = response_service.reference_answer(state)
        state["waiting_for_user_input"] = True
    elif state.get("current_question"):
        reply = response_service.question(state)
        state["waiting_for_user_input"] = True
    else:
        reply = DEFAULT_SAFE_REPLY
        state["waiting_for_user_input"] = True

    state["bot_reply"] = reply
    return state

```

## app/graph/nodes/generate_question.py
```py
"""Question generation node."""

import json

from app.graph.state import InterviewState
from app.llm.client import LLMClientError, OllamaLLMClient
from app.llm.message_factory import build_question_messages
from app.utils.logger import get_logger

logger = get_logger(__name__)

QUESTION_FALLBACKS = [
    ("what_is_goroutine", "Что такое goroutine в Go и зачем она нужна?"),
    ("what_is_channel", "Что такое channel в Go и как он помогает goroutine взаимодействовать?"),
    ("mutex_vs_channel", "Когда в Go лучше использовать mutex, а когда channel?"),
]


def make_generate_question_node(llm_client: OllamaLLMClient):
    def generate_question(state: InterviewState) -> InterviewState:
        try:
            content = llm_client.invoke(build_question_messages(state))
            payload = _extract_question_payload(content)
            key = payload.get("question_key", "")
            question = payload.get("question", "")
            if not key or not question:
                raise ValueError("Question JSON misses fields")
        except (LLMClientError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Question generation fallback used: %s", exc)
            key, question = _fallback_question(state)

        state["current_question_key"] = key
        state["current_question"] = question
        state["current_question_index"] = int(state.get("current_question_index", 0)) + 1
        state["current_answer"] = ""
        state["pending_action"] = "ask_question"
        state["waiting_for_user_input"] = True
        state["tool_result"] = ""
        state["last_tool_used"] = None
        return state

    return generate_question


def _extract_question_payload(content: str) -> dict:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON in question response")
    return json.loads(content[start : end + 1])


def _fallback_question(state: InterviewState) -> tuple[str, str]:
    asked = {item.get("question_key") for item in state.get("history", [])}
    for key, question in QUESTION_FALLBACKS:
        if key not in asked:
            return key, question
    return QUESTION_FALLBACKS[len(asked) % len(QUESTION_FALLBACKS)]

```

## app/graph/nodes/init_interview.py
```py
"""Node that starts a fresh interview."""

from app.graph.state import InterviewState


def init_interview(state: InterviewState) -> InterviewState:
    state["interview_started"] = True
    state["waiting_for_user_input"] = False
    state["pending_action"] = "ask_question"
    state["current_answer"] = ""
    state["error"] = ""
    return state

```

## app/graph/nodes/save_round.py
```py
"""Node that appends the completed QA round to history."""

from app.graph.state import InterviewState


def save_round(state: InterviewState) -> InterviewState:
    history = list(state.get("history", []))
    question_key = state.get("current_question_key", "")

    already_saved = any(
        item.get("question_index") == state.get("current_question_index")
        and item.get("question_key") == question_key
        for item in history
    )
    if not already_saved and question_key and state.get("current_answer"):
        history.append(
            {
                "question_index": state.get("current_question_index", 0),
                "question_key": question_key,
                "question": state.get("current_question", ""),
                "answer": state.get("current_answer", ""),
                "score": state.get("current_score", 0),
                "verdict": state.get("current_verdict", "medium"),
                "feedback": state.get("current_feedback", ""),
                "missing_points": state.get("current_missing_points", []),
            }
        )
    state["history"] = history
    return state

```

## app/graph/prompts/__init__.py
```py


```

## app/graph/prompts/decision_prompts.py
```py
"""Prompt fragments for agent routing decisions."""

DECISION_SYSTEM_PROMPT = """
Ты управляющий интервью. Выбери ровно одно следующее действие.
Доступные action: ask_question, clarify, generate_hint, get_reference_answer, finish.
Доступные difficulty_change: up, keep, down.
Правила:
- finish, если достигнут max_questions или интервью явно пора завершить.
- clarify, если ответ слишком короткий или непонятный и стоит дать кандидату шанс уточнить.
- generate_hint, если кандидат застрял, но вопрос ещё можно спасти.
- get_reference_answer, если нужно показать эталон перед движением дальше.
- ask_question, если можно перейти к следующему вопросу.
Верни JSON: {"action":"...","difficulty_change":"...","reason":"..."}.
""".strip()

DECISION_HUMAN_TEMPLATE = """
Тема: {topic}
Уровень: {level}
Текущий номер вопроса: {question_index}
Максимум вопросов: {max_questions}
Вопрос: {question}
Ответ: {answer}
Оценка: {score}
Вердикт: {verdict}
Feedback: {feedback}
Missing points: {missing_points}
История: {history}

Выбери следующее действие.
""".strip()

```

## app/graph/prompts/evaluation_prompts.py
```py
"""Prompt fragments for answer evaluation."""

EVALUATION_SYSTEM_PROMPT = """
Ты объективный оценщик технического собеседования. Оценивай только ответ кандидата.
Верни JSON строго по схеме: score 0-10, verdict strong|medium|weak, feedback, missing_points.
Пиши feedback на русском языке, коротко и полезно.
""".strip()

EVALUATION_HUMAN_TEMPLATE = """
Тема: {topic}
Уровень: {level}
Вопрос: {question}
Ключ вопроса: {question_key}
Ответ кандидата: {answer}

Оцени ответ. Не задавай новый вопрос.
""".strip()

```

## app/graph/prompts/question_prompts.py
```py
"""Prompt fragments for question generation."""

QUESTION_SYSTEM_PROMPT = """
Ты строгий технический интервьюер. Ты проводишь mock interview на русском языке.
Генерируй ровно один вопрос. Вопрос должен соответствовать теме, уровню и истории.
Используй только один из допустимых question_key: what_is_goroutine, what_is_channel, mutex_vs_channel.
Не повторяй уже заданные вопросы, если есть доступные новые ключи.
Верни короткий JSON: {"question": "...", "question_key": "..."}.
""".strip()

QUESTION_HUMAN_TEMPLATE = """
Тема: {topic}
Уровень: {level}
Уже заданные ключи: {asked_keys}
Номер следующего вопроса: {question_number}

Сгенерируй следующий вопрос для кандидата.
""".strip()

```

## app/graph/prompts/review_prompts.py
```py
"""Prompt fragments for the final mentor review."""

REVIEW_SYSTEM_PROMPT = """
Ты наставник по техническим собеседованиям. Дай финальный review на русском языке.
Будь честным, конкретным и поддерживающим.
Верни JSON строго по схеме: summary, strong_sides, weak_sides, improvement_plan.
""".strip()

REVIEW_HUMAN_TEMPLATE = """
Тема: {topic}
Уровень: {level}
История интервью: {history}

Составь итоговый feedback для кандидата.
""".strip()

```

## app/graph/routers/__init__.py
```py


```

## app/graph/routers/decision_router.py
```py
"""LangGraph router for the action selected by the decision node."""

from app.graph.state import InterviewState
from app.utils.validators import normalize_action


def route_by_decision(state: InterviewState) -> str:
    """Return the next graph edge label from state['pending_action']."""

    return normalize_action(state.get("pending_action", "clarify"))

```

## app/graph/state.py
```py
"""Shared LangGraph state definition.

LangGraph passes this mapping between nodes. The service saves the same shape as
JSON, so the state intentionally contains only JSON-serializable values.
"""

from typing import Any, TypedDict


class InterviewState(TypedDict, total=False):
    user_id: int
    chat_id: int
    interview_started: bool
    topic: str
    current_level: str
    max_questions: int
    current_question_index: int
    current_question: str
    current_question_key: str
    current_answer: str
    current_score: int
    current_verdict: str
    current_feedback: str
    current_missing_points: list[str]
    pending_action: str
    last_tool_used: str | None
    tool_result: str
    waiting_for_user_input: bool
    history: list[dict[str, Any]]
    final_summary: str
    strong_sides: list[str]
    weak_sides: list[str]
    improvement_plan: list[str]
    bot_reply: str
    retry_count: int
    error: str


def create_default_state(
    user_id: int,
    chat_id: int,
    topic: str,
    level: str,
    max_questions: int,
) -> InterviewState:
    """Build a fresh interview state for an API user."""

    return {
        "user_id": user_id,
        "chat_id": chat_id,
        "interview_started": False,
        "topic": topic,
        "current_level": level,
        "max_questions": max_questions,
        "current_question_index": 0,
        "current_question": "",
        "current_question_key": "",
        "current_answer": "",
        "current_score": 0,
        "current_verdict": "medium",
        "current_feedback": "",
        "current_missing_points": [],
        "pending_action": "ask_question",
        "last_tool_used": None,
        "tool_result": "",
        "waiting_for_user_input": False,
        "history": [],
        "final_summary": "",
        "strong_sides": [],
        "weak_sides": [],
        "improvement_plan": [],
        "bot_reply": "",
        "retry_count": 0,
        "error": "",
    }

```

## app/llm/__init__.py
```py


```

## app/llm/client.py
```py
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

```

## app/llm/message_factory.py
```py
"""Factory for role-separated LangChain messages.

The code deliberately uses SystemMessage and HumanMessage instead of one large
string prompt. This makes the examples useful for learning LangGraph/LangChain
message design and keeps instructions clearer for small local models.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.prompts.decision_prompts import DECISION_HUMAN_TEMPLATE, DECISION_SYSTEM_PROMPT
from app.graph.prompts.evaluation_prompts import EVALUATION_HUMAN_TEMPLATE, EVALUATION_SYSTEM_PROMPT
from app.graph.prompts.question_prompts import QUESTION_HUMAN_TEMPLATE, QUESTION_SYSTEM_PROMPT
from app.graph.prompts.review_prompts import REVIEW_HUMAN_TEMPLATE, REVIEW_SYSTEM_PROMPT
from app.graph.state import InterviewState


def build_question_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    asked_keys = [item.get("question_key", "") for item in state.get("history", [])]
    human = QUESTION_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("current_level", "junior"),
        asked_keys=asked_keys,
        question_number=state.get("current_question_index", 0) + 1,
    )
    return [SystemMessage(content=QUESTION_SYSTEM_PROMPT), HumanMessage(content=human)]


def build_evaluation_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    human = EVALUATION_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("current_level", "junior"),
        question=state.get("current_question", ""),
        question_key=state.get("current_question_key", ""),
        answer=state.get("current_answer", ""),
    )
    return [SystemMessage(content=EVALUATION_SYSTEM_PROMPT), HumanMessage(content=human)]


def build_decision_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    human = DECISION_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("current_level", "junior"),
        question_index=state.get("current_question_index", 0),
        max_questions=state.get("max_questions", 3),
        question=state.get("current_question", ""),
        answer=state.get("current_answer", ""),
        score=state.get("current_score", 0),
        verdict=state.get("current_verdict", "medium"),
        feedback=state.get("current_feedback", ""),
        missing_points=state.get("current_missing_points", []),
        history=state.get("history", []),
    )
    return [SystemMessage(content=DECISION_SYSTEM_PROMPT), HumanMessage(content=human)]


def build_review_messages(state: InterviewState) -> list[SystemMessage | HumanMessage]:
    human = REVIEW_HUMAN_TEMPLATE.format(
        topic=state.get("topic", "golang_backend"),
        level=state.get("current_level", "junior"),
        history=state.get("history", []),
    )
    return [SystemMessage(content=REVIEW_SYSTEM_PROMPT), HumanMessage(content=human)]

```

## app/main.py
```py
"""Entrypoint for the HTTP API and browser chat UI.

The app is expected to run in Docker. Uvicorn imports the `app` object from this
module and serves both REST endpoints and a lightweight local chat page.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routes import router
from app.config import get_settings
from app.utils.logger import configure_logging
from app.web.chat_page import CHAT_HTML

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Interview Mentor Agent",
    description="Docker-first mock interview mentor built with LangGraph, Ollama, JSON sessions, and a local chat UI.",
    version="0.1.0",
)
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    """Serve the browser chat UI."""

    return CHAT_HTML

```

## app/schemas/__init__.py
```py


```

## app/schemas/api.py
```py
"""HTTP API schemas for the interview mentor service."""

from typing import Any

from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    """Request body for starting or resetting an interview."""

    user_id: int = Field(description="Stable user/session identifier")
    chat_id: int | None = Field(default=None, description="Optional client conversation id")


class AnswerRequest(BaseModel):
    """Request body with the candidate answer for the current question."""

    user_id: int
    chat_id: int | None = None
    text: str = Field(min_length=1)


class InterviewResponse(BaseModel):
    """Response returned to API clients after every interview step."""

    user_id: int
    reply: str
    state: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    transport: str

```

## app/schemas/decision.py
```py
"""Pydantic schemas for routing decisions made by the agent."""

from typing import Literal

from pydantic import BaseModel, field_validator

from app.utils.validators import normalize_action, normalize_difficulty_change


class DecisionResult(BaseModel):
    """Structured output returned by the interview manager node."""

    action: Literal["ask_question", "clarify", "generate_hint", "get_reference_answer", "finish"]
    difficulty_change: Literal["up", "keep", "down"] = "keep"
    reason: str

    @field_validator("action", mode="before")
    @classmethod
    def validate_action(cls, value: str) -> str:
        return normalize_action(str(value))

    @field_validator("difficulty_change", mode="before")
    @classmethod
    def validate_difficulty_change(cls, value: str) -> str:
        return normalize_difficulty_change(str(value))

```

## app/schemas/evaluation.py
```py
"""Pydantic schemas for answer evaluation."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import clamp_score, normalize_verdict


class EvaluationResult(BaseModel):
    """Structured output returned by the answer evaluator node."""

    score: int = Field(description="Answer score from 0 to 10")
    verdict: Literal["strong", "medium", "weak"] = "medium"
    feedback: str
    missing_points: list[str] = Field(default_factory=list)

    @field_validator("score", mode="before")
    @classmethod
    def validate_score(cls, value: int) -> int:
        return clamp_score(value)

    @field_validator("verdict", mode="before")
    @classmethod
    def validate_verdict(cls, value: str) -> str:
        return normalize_verdict(str(value))

```

## app/schemas/review.py
```py
"""Pydantic schemas for the final interview review."""

from pydantic import BaseModel, Field


class FinalReviewResult(BaseModel):
    """Structured output returned by the final mentor node."""

    summary: str
    strong_sides: list[str] = Field(default_factory=list)
    weak_sides: list[str] = Field(default_factory=list)
    improvement_plan: list[str] = Field(default_factory=list)

```

## app/services/__init__.py
```py


```

## app/services/interview_service.py
```py
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

```

## app/services/response_service.py
```py
"""Formatting user-facing HTTP API responses from graph state."""

from app.graph.state import InterviewState


class ResponseService:
    """Central place for response templates returned by the API."""

    def question(self, state: InterviewState) -> str:
        return (
            f"Вопрос {state.get('current_question_index', 1)}/{state.get('max_questions', 3)} "
            f"({state.get('topic')} / {state.get('current_level')}):\n\n"
            f"{state.get('current_question')}"
        )

    def clarify(self, state: InterviewState) -> str:
        return (
            "Хочу чуть точнее понять ваш ответ.\n\n"
            f"Комментарий: {state.get('current_feedback', 'Нужно больше деталей.')}\n\n"
            "Уточните, пожалуйста, ответ на тот же вопрос."
        )

    def hint(self, state: InterviewState) -> str:
        return f"Подсказка:\n\n{state.get('tool_result')}\n\nПопробуйте ответить на тот же вопрос ещё раз."

    def reference_answer(self, state: InterviewState) -> str:
        return f"Эталонный ответ:\n\n{state.get('tool_result')}\n\nМожете продолжить: напишите любой текст, и я выберу следующий шаг."

    def final_review(self, state: InterviewState) -> str:
        strong = self._format_list(state.get("strong_sides", []))
        weak = self._format_list(state.get("weak_sides", []))
        plan = self._format_list(state.get("improvement_plan", []))
        return (
            "Итог интервью:\n\n"
            f"{state.get('final_summary', 'Интервью завершено.')}\n\n"
            f"Сильные стороны:\n{strong}\n\n"
            f"Зоны роста:\n{weak}\n\n"
            f"План улучшения:\n{plan}"
        )

    def fallback(self, state: InterviewState) -> str:
        return state.get("bot_reply") or "Готов продолжать интервью."

    @staticmethod
    def _format_list(items: list[str]) -> str:
        if not items:
            return "- Пока недостаточно данных"
        return "\n".join(f"- {item}" for item in items)

```

## app/services/session_service.py
```py
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

```

## app/storage/__init__.py
```py


```

## app/storage/json_store.py
```py
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

```

## app/storage/session_repository.py
```py
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

```

## app/storage/sessions/.gitkeep
```gitkeep


```

## app/tools/__init__.py
```py


```

## app/tools/data/hints.json
```json
{
  "golang_backend": {
    "junior": {
      "what_is_goroutine": "Вспомните ключевое слово go, лёгкость goroutine и то, что ими управляет runtime scheduler.",
      "what_is_channel": "Подумайте про типизированную передачу данных между goroutine и синхронизацию отправки/получения.",
      "mutex_vs_channel": "Сравните две идеи: mutex защищает общую память, channel помогает обмениваться сообщениями и координировать работу."
    }
  }
}

```

## app/tools/data/reference_answers.json
```json
{
  "golang_backend": {
    "junior": {
      "what_is_goroutine": "Goroutine - это легковесный поток выполнения в Go, запускаемый через ключевое слово go. Планировщик Go распределяет goroutine по системным потокам, поэтому можно создавать тысячи конкурентных задач дешевле, чем OS threads.",
      "what_is_channel": "Channel - это типизированный канал для обмена данными между goroutine. Он помогает синхронизировать выполнение и передавать значения безопаснее, чем общая память без контроля.",
      "mutex_vs_channel": "Mutex защищает критическую секцию и общий state, когда нескольким goroutine нужен доступ к одним данным. Channel лучше подходит для передачи владения данными и координации потоков выполнения. В Go часто выбирают channel для коммуникации, а mutex - для простой защиты shared state."
    }
  }
}

```

## app/tools/hint_tool.py
```py
"""Local hint tool backed by JSON data."""

from pathlib import Path

from app.storage.json_store import JsonStore

FALLBACK_HINT = (
    "Подсказка для этого вопроса пока не найдена. "
    "Попробуйте ответить по схеме: что это, зачем нужно, где применяется."
)


def generate_hint(topic: str, level: str, question_key: str) -> str:
    """Return a hint from app/tools/data/hints.json."""

    data_path = Path(__file__).parent / "data" / "hints.json"
    data = JsonStore().read(data_path, default={})
    return data.get(topic, {}).get(level, {}).get(question_key, FALLBACK_HINT)

```

## app/tools/reference_tool.py
```py
"""Local reference-answer tool backed by JSON data."""

from pathlib import Path

from app.storage.json_store import JsonStore

FALLBACK_REFERENCE = (
    "Эталонный ответ для этого вопроса пока не найден. "
    "Попробуйте сформулировать ответ через определение, назначение и короткий пример."
)


def get_reference_answer(topic: str, level: str, question_key: str) -> str:
    """Return a reference answer from app/tools/data/reference_answers.json."""

    data_path = Path(__file__).parent / "data" / "reference_answers.json"
    data = JsonStore().read(data_path, default={})
    return data.get(topic, {}).get(level, {}).get(question_key, FALLBACK_REFERENCE)

```

## app/tools/tool_registry.py
```py
"""Registry for local interview tools.

No external MCP SDK is used here. The registry is intentionally just a small
mapping of tool names to Python callables so students can see the mechanics.
"""

from collections.abc import Callable

from app.tools.hint_tool import generate_hint
from app.tools.reference_tool import get_reference_answer


class ToolRegistry:
    """Lookup and execute local tools by name."""

    def __init__(self) -> None:
        self._tools: dict[str, Callable[[str, str, str], str]] = {
            "generate_hint": generate_hint,
            "get_reference_answer": get_reference_answer,
        }

    def run(self, tool_name: str, topic: str, level: str, question_key: str) -> str:
        tool = self._tools.get(tool_name)
        if tool is None:
            return "Инструмент не найден. Попробуем продолжить интервью без него."
        return tool(topic, level, question_key)

    @property
    def names(self) -> list[str]:
        return sorted(self._tools.keys())

```

## app/utils/__init__.py
```py


```

## app/utils/constants.py
```py
"""Constants used across the interview workflow."""

DEFAULT_SAFE_REPLY = (
    "Сейчас я не смог корректно обработать шаг интервью. "
    "Попробуйте ответить ещё раз или используйте /reset для нового интервью."
)

OLLAMA_UNAVAILABLE_REPLY = (
    "Модель Ollama пока недоступна. Проверьте, что контейнер ollama запущен "
    "и модель llama3.2:1b уже загружена."
)

ALLOWED_ACTIONS = {"ask_question", "clarify", "generate_hint", "get_reference_answer", "finish"}
ALLOWED_DIFFICULTY_CHANGES = {"up", "keep", "down"}
LEVEL_ORDER = ["junior", "middle", "senior"]

```

## app/utils/logger.py
```py
"""Logging helpers for consistent console logs in Docker."""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

```

## app/utils/validators.py
```py
"""Validation and normalization helpers for model outputs."""

from app.utils.constants import ALLOWED_ACTIONS, ALLOWED_DIFFICULTY_CHANGES


def clamp_score(score: int) -> int:
    """Normalize a model score to the 0..10 interval."""

    return max(0, min(10, int(score)))


def normalize_verdict(verdict: str) -> str:
    return verdict if verdict in {"strong", "medium", "weak"} else "medium"


def normalize_action(action: str) -> str:
    return action if action in ALLOWED_ACTIONS else "clarify"


def normalize_difficulty_change(change: str) -> str:
    return change if change in ALLOWED_DIFFICULTY_CHANGES else "keep"

```

## app/web/__init__.py
```py


```

## app/web/chat_page.py
```py
"""HTML page for a lightweight local chat interface."""

CHAT_HTML = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Interview Mentor</title>
  <style>
    :root {
      --ink: #17211b;
      --muted: #657267;
      --paper: #fffaf0;
      --panel: rgba(255, 250, 240, 0.86);
      --line: rgba(23, 33, 27, 0.16);
      --accent: #e05d2f;
      --accent-dark: #a33c1d;
      --sage: #57745b;
      --bot: #f5e6c8;
      --user: #dbe9d1;
      --shadow: 0 24px 70px rgba(42, 31, 18, 0.2);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at 15% 15%, rgba(224, 93, 47, 0.22), transparent 28rem),
        radial-gradient(circle at 85% 5%, rgba(87, 116, 91, 0.24), transparent 24rem),
        linear-gradient(135deg, #f3dfb8 0%, #fffaf0 46%, #cad9b7 100%);
    }

    .grain {
      min-height: 100vh;
      padding: 32px;
      background-image: linear-gradient(rgba(23, 33, 27, 0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(23, 33, 27, 0.03) 1px, transparent 1px);
      background-size: 22px 22px;
    }

    .shell {
      width: min(1120px, 100%);
      margin: 0 auto;
      display: grid;
      grid-template-columns: 330px minmax(0, 1fr);
      gap: 24px;
      align-items: stretch;
    }

    .card {
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }

    .sidebar { padding: 28px; }

    .eyebrow {
      margin: 0 0 12px;
      color: var(--accent-dark);
      font: 700 12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }

    h1 {
      margin: 0;
      font-size: clamp(34px, 6vw, 58px);
      line-height: 0.92;
      letter-spacing: -0.05em;
    }

    .lead {
      margin: 20px 0 0;
      color: var(--muted);
      font-size: 17px;
      line-height: 1.55;
    }

    .controls {
      margin-top: 26px;
      display: grid;
      gap: 12px;
    }

    label {
      display: grid;
      gap: 8px;
      color: var(--muted);
      font: 700 12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    input, textarea, button {
      font: inherit;
    }

    input, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 13px 14px;
      color: var(--ink);
      background: rgba(255, 255, 255, 0.58);
      outline: none;
    }

    input:focus, textarea:focus { border-color: rgba(224, 93, 47, 0.7); }

    .button-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 6px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 16px;
      cursor: pointer;
      color: #fffaf0;
      background: var(--ink);
      transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }

    button:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(23, 33, 27, 0.18); }
    button:disabled { cursor: wait; opacity: 0.64; transform: none; }

    .primary { background: var(--accent); }
    .secondary { background: var(--sage); }
    .ghost { background: rgba(23, 33, 27, 0.72); }

    .chat-card {
      display: grid;
      grid-template-rows: auto 1fr auto;
      min-height: calc(100vh - 64px);
      overflow: hidden;
    }

    .chat-top {
      padding: 20px 24px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }

    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font: 700 12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #83aa62;
      box-shadow: 0 0 0 6px rgba(131, 170, 98, 0.16);
    }

    .messages {
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .message {
      max-width: min(680px, 88%);
      padding: 16px 18px;
      border-radius: 22px;
      line-height: 1.5;
      white-space: pre-wrap;
      animation: rise 220ms ease both;
    }

    .bot {
      align-self: flex-start;
      background: var(--bot);
      border-top-left-radius: 6px;
    }

    .user {
      align-self: flex-end;
      background: var(--user);
      border-top-right-radius: 6px;
    }

    .composer {
      padding: 18px;
      border-top: 1px solid var(--line);
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: end;
    }

    textarea {
      min-height: 58px;
      max-height: 180px;
      resize: vertical;
    }

    .send { padding-inline: 24px; min-height: 58px; }

    @keyframes rise {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 860px) {
      .grain { padding: 16px; }
      .shell { grid-template-columns: 1fr; }
      .chat-card { min-height: 68vh; }
      .composer { grid-template-columns: 1fr; }
      .send { width: 100%; }
    }
  </style>
</head>
<body>
  <main class="grain">
    <section class="shell">
      <aside class="card sidebar">
        <p class="eyebrow">LangGraph + Ollama</p>
        <h1>Mock interview, но без лишней драмы</h1>
        <p class="lead">Локальный чат для учебного агента. Начните интервью, отвечайте на вопросы, а агент сам решит: уточнить, дать подсказку, показать эталон или завершить.</p>
        <div class="controls">
          <label>User ID<input id="userId" type="number" min="1" value="1" /></label>
          <div class="button-row">
            <button class="primary" id="startBtn">Начать</button>
            <button class="secondary" id="finishBtn">Завершить</button>
          </div>
          <button class="ghost" id="resetBtn">Сбросить сессию</button>
        </div>
      </aside>

      <section class="card chat-card">
        <header class="chat-top">
          <div>
            <p class="eyebrow">Interview Mentor</p>
            <strong>golang_backend / junior</strong>
          </div>
          <span class="status"><i class="dot"></i><span id="statusText">ready</span></span>
        </header>
        <div class="messages" id="messages"></div>
        <form class="composer" id="form">
          <textarea id="answer" placeholder="Напишите ответ кандидата..." required></textarea>
          <button class="primary send" type="submit">Отправить</button>
        </form>
      </section>
    </section>
  </main>

  <script>
    const messages = document.querySelector('#messages');
    const userId = document.querySelector('#userId');
    const answer = document.querySelector('#answer');
    const form = document.querySelector('#form');
    const statusText = document.querySelector('#statusText');
    const buttons = [...document.querySelectorAll('button')];

    function addMessage(role, text) {
      const node = document.createElement('div');
      node.className = `message ${role}`;
      node.textContent = text;
      messages.appendChild(node);
      messages.scrollTop = messages.scrollHeight;
    }

    function setBusy(isBusy, label = 'ready') {
      statusText.textContent = label;
      buttons.forEach((button) => { button.disabled = isBusy; });
    }

    async function callApi(path, payload) {
      setBusy(true, 'thinking');
      try {
        const response = await fetch(path, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          const text = await response.text();
          throw new Error(`${response.status}: ${text}`);
        }
        const data = await response.json();
        addMessage('bot', data.reply);
      } catch (error) {
        addMessage('bot', `Ошибка API: ${error.message}`);
      } finally {
        setBusy(false);
      }
    }

    document.querySelector('#startBtn').addEventListener('click', () => {
      messages.innerHTML = '';
      callApi('/interviews/start', { user_id: Number(userId.value || 1) });
    });

    document.querySelector('#resetBtn').addEventListener('click', () => {
      messages.innerHTML = '';
      callApi('/interviews/reset', { user_id: Number(userId.value || 1) });
    });

    document.querySelector('#finishBtn').addEventListener('click', () => {
      callApi('/interviews/finish', { user_id: Number(userId.value || 1) });
    });

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      const text = answer.value.trim();
      if (!text) return;
      addMessage('user', text);
      answer.value = '';
      callApi('/interviews/answer', { user_id: Number(userId.value || 1), text });
    });

    addMessage('bot', 'Привет. Нажмите «Начать», и я задам первый вопрос.');
  </script>
</body>
</html>
"""

```

## docker/app/docker-entrypoint.sh
```sh
#!/bin/sh
set -eu

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
SESSIONS_DIR="${SESSIONS_DIR:-/app/app/storage/sessions}"

echo "Waiting for Ollama at ${OLLAMA_BASE_URL}..."
until curl -fsS "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; do
  sleep 2
done

mkdir -p "${SESSIONS_DIR}"

echo "Ollama is ready. Starting Interview Mentor API..."
exec "$@"
```

## docker/app/Dockerfile
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY tests /app/tests
COPY scripts /app/scripts
COPY docker/app/docker-entrypoint.sh /app/docker/app/docker-entrypoint.sh

RUN chmod +x /app/docker/app/docker-entrypoint.sh

ENTRYPOINT ["/bin/sh", "/app/docker/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

```

## docker/ollama/init-model.sh
```sh
#!/bin/sh
set -eu

OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:1b}"

# The official ollama image does not always include curl/wget, so readiness is
# checked through the ollama CLI itself. OLLAMA_HOST is provided by compose.
echo "Waiting for Ollama API at ${OLLAMA_HOST:-http://ollama:11434}..."
until ollama list >/dev/null 2>&1; do
  sleep 2
done

if ollama list | awk '{print $1}' | grep -qx "${OLLAMA_MODEL}"; then
  echo "Model ${OLLAMA_MODEL} already exists."
else
  echo "Pulling model ${OLLAMA_MODEL}..."
  ollama pull "${OLLAMA_MODEL}"
fi

echo "Ollama model initialization completed."
```

## docker-compose.yml
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: interview_mentor_ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 10s

  ollama_init:
    image: ollama/ollama:latest
    container_name: interview_mentor_ollama_init
    depends_on:
      ollama:
        condition: service_healthy
    environment:
      OLLAMA_HOST: http://ollama:11434
      OLLAMA_BASE_URL: http://ollama:11434
      OLLAMA_MODEL: ${OLLAMA_MODEL:-llama3.2:1b}
    volumes:
      - ollama_data:/root/.ollama
      - ./docker/ollama/init-model.sh:/init-model.sh:ro
    entrypoint: ["/bin/sh", "/init-model.sh"]
    restart: "no"

  app:
    build:
      context: .
      dockerfile: docker/app/Dockerfile
    container_name: interview_mentor_api
    depends_on:
      ollama:
        condition: service_healthy
      ollama_init:
        condition: service_completed_successfully
    ports:
      - "8000:8000"
    environment:
      APP_HOST: ${APP_HOST:-0.0.0.0}
      APP_PORT: ${APP_PORT:-8000}
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://ollama:11434}
      OLLAMA_MODEL: ${OLLAMA_MODEL:-llama3.2:1b}
      MAX_QUESTIONS: ${MAX_QUESTIONS:-3}
      DEFAULT_TOPIC: ${DEFAULT_TOPIC:-golang_backend}
      DEFAULT_LEVEL: ${DEFAULT_LEVEL:-junior}
      SESSIONS_DIR: ${SESSIONS_DIR:-/app/app/storage/sessions}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    volumes:
      - sessions_data:/app/app/storage/sessions
    restart: unless-stopped

volumes:
  ollama_data:
  sessions_data:

```

## graph.mmd
```mmd
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	init_interview(init_interview)
	generate_question(generate_question)
	evaluate_answer(evaluate_answer)
	agent_decision(agent_decision)
	adjust_difficulty(adjust_difficulty)
	save_round(save_round)
	final_review(final_review)
	format_output(format_output)
	generate_hint(generate_hint)
	get_reference_answer(get_reference_answer)
	__end__([<p>__end__</p>]):::last
	__start__ -.-> evaluate_answer;
	__start__ -.-> init_interview;
	__start__ -.-> save_round;
	adjust_difficulty --> save_round;
	agent_decision -. &nbsp;ask_question&nbsp; .-> adjust_difficulty;
	agent_decision -. &nbsp;clarify&nbsp; .-> format_output;
	agent_decision -.-> generate_hint;
	agent_decision -.-> get_reference_answer;
	agent_decision -. &nbsp;finish&nbsp; .-> save_round;
	evaluate_answer --> agent_decision;
	final_review --> format_output;
	generate_hint --> format_output;
	generate_question --> format_output;
	get_reference_answer --> format_output;
	init_interview --> generate_question;
	save_round -.-> final_review;
	save_round -.-> generate_question;
	format_output --> __end__;
	save_round -.-> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```

## README.md
```md
# Interview Mentor API

`Interview Mentor API` - учебный AI-агент для mock interview по техническим темам. Проект показывает, как собрать понятный LangGraph workflow вокруг локальной LLM в Ollama, сохранить состояние пользователя в JSON и дать удобный интерфейс через браузерный чат. Всё запускается через Docker Compose: Python, FastAPI, Ollama, модель и окружение живут в контейнерах.

![LangGraph workflow](./graph.png)

## Что умеет проект

Проект умеет запускаться полностью через Docker Compose, автоматически поднимать Ollama и загружать модель `llama3.2:1b`, открывать локальный веб-чат на `http://localhost:8000`, начинать mock interview, задавать вопросы по теме `golang_backend`, принимать ответы пользователя, оценивать ответы через LLM, выбирать следующий шаг через LangGraph, просить уточнение, выдавать подсказку, показывать эталонный ответ, сохранять состояние сессии в JSON, завершать интервью с итоговым feedback, а также предоставлять REST API и Swagger UI для тестирования без Telegram и внешних bot API.

## Короткое описание графа

Граф симулирует работу AI-наставника по техническому собеседованию: агент начинает mock interview, задаёт вопрос, принимает ответ пользователя, оценивает его, сам выбирает следующий шаг и в конце выдаёт итоговый feedback. Узлы: `init_interview`, `generate_question`, `evaluate_answer`, `agent_decision`, `adjust_difficulty`, `save_round`, `generate_hint`, `get_reference_answer`, `final_review`, `format_output`. Рёбра: интервью начато, вопрос задан, ответ оценён, решение принято, сложность изменена, раунд сохранён, подсказка получена, эталонный ответ показан, финальный review создан, интервью завершено. State: сессия пользователя с темой, уровнем, текущим вопросом, ответом, оценкой, feedback, history, выбранным действием и итоговым review. Модель: `llama3.2:1b` через Ollama для генерации вопросов, оценки ответов, выбора действия и финального feedback.

## Архитектура

Проект разделён на несколько слоёв, чтобы его было удобно читать и расширять:

- `app/api` - HTTP endpoints FastAPI.
- `app/web` - встроенный браузерный чат без отдельной frontend-сборки.
- `app/services` - orchestration use-cases: интервью, сессии, форматирование ответов.
- `app/graph` - LangGraph state machine, nodes, routers и prompts.
- `app/llm` - клиент Ollama и фабрика `SystemMessage` / `HumanMessage`.
- `app/tools` - локальные tools на JSON-файлах: подсказки и эталонные ответы.
- `app/storage` - JSON-хранилище сессий.
- `app/schemas` - Pydantic-схемы для structured output и HTTP API.
- `scripts` - вспомогательные скрипты, включая генерацию `graph.png`.
- `docker` - Dockerfile и entrypoint-скрипты.

## Использованные библиотеки

| Библиотека | Для чего используется |
|---|---|
| `FastAPI` | HTTP API и выдача HTML-чата |
| `Uvicorn` | ASGI-сервер внутри контейнера `app` |
| `LangGraph` | Построение графа интервью и маршрутизация между узлами |
| `LangChain Core` | Сообщения `SystemMessage` и `HumanMessage` |
| `langchain-ollama` | Подключение к Ollama как к chat model |
| `Pydantic` | Structured output, валидация LLM-ответов и API-схем |
| `pydantic-settings` | Настройки через переменные окружения |
| | `pytest` | Тесты tools, router, схем и session storage |
| `httpx` | HTTP-клиент, полезен для тестов и диагностики |

## Использованные модели и роли

В проекте используется одна локальная модель: `llama3.2:1b` через Ollama. Она работает в нескольких ролях, заданных через отдельные prompts и раздельные `SystemMessage` / `HumanMessage`.

| Узел | Модель | Роль |
|---|---|---|
| `generate_question` | `llama3.2:1b` | Строгий технический интервьюер, который генерирует следующий вопрос |
| `evaluate_answer` | `llama3.2:1b` | Объективный оценщик, который возвращает `EvaluationResult` |
| `agent_decision` | `llama3.2:1b` | Управляющий интервью, который выбирает следующее действие |
| `final_review` | `llama3.2:1b` | Наставник, который составляет итоговый review |

Локальные tools не используют отдельную модель. `generate_hint` достаёт подсказку из `app/tools/data/hints.json`, а `get_reference_answer` достаёт эталонный ответ из `app/tools/data/reference_answers.json`.

## State графа

State хранится как обычный JSON-совместимый словарь `InterviewState`. Один пользователь = один JSON-файл в session storage.

Основные поля state:

- `user_id` - идентификатор пользователя.
- `chat_id` - идентификатор диалога, для HTTP API обычно равен `user_id`.
- `interview_started` - начато ли интервью.
- `topic` - тема интервью, по умолчанию `golang_backend`.
- `current_level` - текущий уровень, по умолчанию `junior`.
- `max_questions` - максимум вопросов, по умолчанию `3`.
- `current_question_index` - номер текущего вопроса.
- `current_question` - текст текущего вопроса.
- `current_question_key` - ключ вопроса для локальных tools.
- `current_answer` - последний ответ пользователя.
- `current_score` - оценка ответа от `0` до `10`.
- `current_verdict` - `strong`, `medium` или `weak`.
- `current_feedback` - комментарий оценщика.
- `current_missing_points` - список недостающих пунктов.
- `pending_action` - действие, выбранное агентом.
- `tool_result` - результат локального tool.
- `history` - история завершённых раундов.
- `final_summary`, `strong_sides`, `weak_sides`, `improvement_plan` - итоговый review.
- `bot_reply` - текст, который возвращается в чат/API.
- `error` - безопасно сохранённая ошибка, если что-то пошло не так.

## Узлы графа

Всего в графе 10 узлов: 7 основных и 3 вспомогательных.

| Узел | Тип | Что делает |
|---|---|---|
| `init_interview` | Основной | Начинает новую сессию интервью, выставляет стартовые флаги и готовит state к первому вопросу |
| `generate_question` | Основной | Вызывает LLM, генерирует один вопрос и `question_key`, учитывая тему, уровень и историю |
| `evaluate_answer` | Основной | Вызывает LLM и получает structured output `EvaluationResult` со score, verdict, feedback и missing points |
| `agent_decision` | Основной | Вызывает LLM и получает `DecisionResult`: что делать дальше и как менять сложность |
| `generate_hint` | Основной | Вызывает локальный JSON tool и возвращает подсказку по текущему вопросу |
| `get_reference_answer` | Основной | Вызывает локальный JSON tool и возвращает эталонный ответ по текущему вопросу |
| `final_review` | Основной | Вызывает LLM и формирует итоговый review по истории интервью |
| `adjust_difficulty` | Вспомогательный | Меняет уровень сложности по решению агента: `up`, `keep`, `down` |
| `save_round` | Вспомогательный | Сохраняет завершённый вопрос-ответ в `history` |
| `format_output` | Вспомогательный | Превращает state в человекочитаемый ответ для браузерного чата и API |

## Рёбра графа

Всего в графе 18 рёбер: 10 основных и 8 вспомогательных. По рёбрам: 10 основных - успешная линия интервью от старта до финального review, плюс ветки уточнения, подсказки и эталонного ответа; 8 вспомогательных - входы в граф, сохранение раунда, форматирование ответа и завершение выполнения.

| Ребро | Тип | Что означает |
|---|---|---|
| `START -> init_interview` | Вспомогательное | Вход в граф для новой сессии |
| `START -> evaluate_answer` | Вспомогательное | Вход в граф, когда пользователь прислал ответ |
| `START -> save_round` | Вспомогательное | Вход в граф, когда пользователь завершает интервью |
| `init_interview -> generate_question` | Основное | Интервью начато, можно задать первый вопрос |
| `generate_question -> format_output` | Вспомогательное | Вопрос нужно подготовить для ответа UI/API |
| `evaluate_answer -> agent_decision` | Основное | Ответ оценён, агент должен выбрать следующий шаг |
| `agent_decision -> adjust_difficulty` | Основное | Агент решил перейти к следующему вопросу |
| `agent_decision -> format_output` | Основное | Агент решил попросить уточнение |
| `agent_decision -> generate_hint` | Основное | Агент решил дать подсказку |
| `agent_decision -> get_reference_answer` | Основное | Агент решил показать эталонный ответ |
| `agent_decision -> save_round` | Основное | Агент решил завершить интервью |
| `adjust_difficulty -> save_round` | Вспомогательное | Сложность обновлена, текущий раунд нужно сохранить |
| `save_round -> generate_question` | Основное | Раунд сохранён, можно задать следующий вопрос |
| `save_round -> final_review` | Основное | Раунд сохранён, пора сформировать итоговый review |
| `generate_hint -> format_output` | Вспомогательное | Подсказку нужно отформатировать для пользователя |
| `get_reference_answer -> format_output` | Вспомогательное | Эталонный ответ нужно отформатировать для пользователя |
| `final_review -> format_output` | Вспомогательное | Итоговый review нужно отформатировать для пользователя |
| `format_output -> END` | Вспомогательное | Ответ готов, выполнение графа завершено |

## Mermaid-схема

```mermaid
flowchart TD
    Start((START))
    End((END))

    Start -->|new session| init_interview
    Start -->|answer| evaluate_answer
    Start -->|finish command| save_round

    init_interview -->|interview started| generate_question
    generate_question -->|question ready| format_output

    evaluate_answer -->|answer evaluated| agent_decision

    agent_decision -->|ask_question| adjust_difficulty
    agent_decision -->|clarify| format_output
    agent_decision -->|generate_hint| generate_hint
    agent_decision -->|get_reference_answer| get_reference_answer
    agent_decision -->|finish| save_round

    adjust_difficulty -->|difficulty changed| save_round
    save_round -->|continue| generate_question
    save_round -->|finish| final_review

    generate_hint -->|hint reply| format_output
    get_reference_answer -->|reference reply| format_output
    final_review -->|summary reply| format_output
    format_output -->|response returned| End
```

## Как запустить проект локально

Локально здесь означает “на вашей машине через Docker”. Запускать Python на хосте не нужно.

1. Убедитесь, что установлен Docker и Docker Compose.

2. Скопируйте переменные окружения:

```bash
cp .env.example .env
```

3. Запустите весь стек:

```bash
docker compose up --build
```

4. Дождитесь, пока `ollama_init` скачает модель. В логах должно быть что-то вроде:

```text
Pulling model llama3.2:1b...
Ollama model initialization completed.
```

Если модель уже скачана, будет:

```text
Model llama3.2:1b already exists.
```

5. Откройте чат в браузере:

```text
http://localhost:8000
```

6. Swagger UI доступен здесь:

```text
http://localhost:8000/docs
```

## Как пользоваться чатом

На странице `http://localhost:8000` можно:

- выбрать `User ID`;
- нажать `Начать`;
- отвечать на вопросы в поле чата;
- нажать `Завершить`, чтобы получить итоговый feedback;
- нажать `Сбросить сессию`, чтобы начать заново.

## Как пользоваться API

Начать интервью:

```bash
curl -X POST http://localhost:8000/interviews/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Ответить на текущий вопрос:

```bash
curl -X POST http://localhost:8000/interviews/answer \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "text": "Goroutine - это легковесный поток выполнения в Go..."}'
```

Завершить интервью:

```bash
curl -X POST http://localhost:8000/interviews/finish \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Сбросить сессию:

```bash
curl -X POST http://localhost:8000/interviews/reset \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Посмотреть сохранённую сессию:

```bash
curl http://localhost:8000/interviews/1/session
```

## Docker Compose

Compose поднимает три сервиса:

| Сервис | Что делает |
|---|---|
| `ollama` | Запускает Ollama API и хранит модели в volume `ollama_data` |
| `ollama_init` | Одноразово проверяет модель и выполняет `ollama pull llama3.2:1b`, если модели нет |
| `app` | Запускает FastAPI, браузерный чат и REST API на порту `8000` |

Volumes:

- `ollama_data` - модели Ollama.
- `sessions_data` - JSON-сессии пользователей.

## Проверка Ollama

Проверить список моделей:

```bash
docker compose exec ollama ollama list
```

Проверить HTTP API Ollama:

```bash
curl http://localhost:11434/api/tags
```

## Генерация картинки графа

Файл `graph.png` уже лежит в корне проекта и используется в README. Если граф изменился, картинку можно перегенерировать. Текущая версия использует первый локальный renderer на `Pillow`: он не зависит от `mermaid.ink`, Node.js, Mermaid CLI или внешнего интернета, поэтому стабильно работает в Docker/WSL.

Через Docker, без локальной установки Python:

```bash
docker compose build app
docker compose run --rm --entrypoint python -v "$PWD:/workspace" app /app/scripts/render_graph_png.py /workspace/graph.png
```

Если Python и зависимости установлены локально, можно так:

```bash
python scripts/render_graph_png.py graph.png
```

## Тесты

Запуск тестов в контейнере:

```bash
docker compose run --rm app pytest
```

Тесты покрывают:

- чтение локальных tools из JSON;
- fallback для tools;
- маршрутизацию по action;
- сохранение и загрузку JSON-сессии;
- нормализацию structured output.

## Ограничения MVP

- Нет базы данных и Redis.
- Нет Telegram, webhook и внешних bot API.
- Нет streaming-ответов, API возвращает готовый результат шага.
- Tools локальные и читают JSON-файлы.
- Данные примеров есть только для `golang_backend / junior`.
- `llama3.2:1b` маленькая модель, поэтому prompts и fallback-и сделаны максимально прямолинейными.
- Для учебной простоты сессии сохраняются целиком в JSON после каждого шага.

## Что можно улучшить дальше

- Вынести HTML/CSS/JS из `app/web/chat_page.py` в полноценные static files.
- Добавить streaming ответа через Server-Sent Events.
- Сделать frontend на React/Vue/Svelte.
- Добавить CLI-клиент для терминального интервью.
- Добавить больше тем и уровней в JSON tools.
- Подключить другой transport отдельным слоем, не меняя LangGraph и services.





```

## requirements.txt
```txt
langgraph>=0.2.60,<0.4.0
langchain-core>=0.3.0,<0.4.0
langchain-ollama>=0.2.0,<0.4.0
fastapi>=0.115.0,<1.0.0
uvicorn[standard]>=0.30.0,<1.0.0
pillow>=10.4,<12.0
pydantic>=2.8,<3.0
pydantic-settings>=2.4,<3.0
pytest>=8.3,<9.0
httpx>=0.27,<1.0

```

## scripts/render_graph_png.py
```py
"""Render the Interview Mentor graph to a PNG file.

This is the first local renderer used in the project: it draws a deterministic
PNG without external services such as mermaid.ink and without Node/Mermaid CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CANVAS_WIDTH = 1800
CANVAS_HEIGHT = 1350
BACKGROUND = (255, 250, 240)
INK = (23, 33, 27)
MUTED = (89, 103, 92)
ACCENT = (224, 93, 47)
SAGE = (87, 116, 91)
PANEL = (245, 230, 200)
TOOL = (219, 233, 209)
LINE = (90, 77, 57)

NODES = {
    "START": (760, 40, 1040, 120, "START", "entry"),
    "init_interview": (120, 210, 420, 310, "init_interview", "start session"),
    "generate_question": (590, 210, 910, 310, "generate_question", "LLM asks question"),
    "format_output": (1180, 210, 1500, 310, "format_output", "reply for chat/API"),
    "evaluate_answer": (120, 460, 420, 560, "evaluate_answer", "LLM scores answer"),
    "agent_decision": (590, 460, 910, 560, "agent_decision", "LLM chooses route"),
    "adjust_difficulty": (1180, 430, 1500, 530, "adjust_difficulty", "up / keep / down"),
    "save_round": (1180, 650, 1500, 750, "save_round", "append history"),
    "generate_hint": (120, 760, 420, 860, "generate_hint", "local JSON tool"),
    "get_reference_answer": (590, 760, 910, 860, "get_reference_answer", "local JSON tool"),
    "final_review": (1180, 890, 1500, 990, "final_review", "LLM final feedback"),
    "END": (760, 1150, 1040, 1230, "END", "done"),
}

EDGES = [
    ("START", "init_interview", "new session"),
    ("START", "evaluate_answer", "answer"),
    ("START", "save_round", "finish command"),
    ("init_interview", "generate_question", "interview started"),
    ("generate_question", "format_output", "question ready"),
    ("evaluate_answer", "agent_decision", "answer evaluated"),
    ("agent_decision", "adjust_difficulty", "ask_question"),
    ("agent_decision", "format_output", "clarify"),
    ("agent_decision", "generate_hint", "hint"),
    ("agent_decision", "get_reference_answer", "reference"),
    ("agent_decision", "save_round", "finish"),
    ("adjust_difficulty", "save_round", "difficulty changed"),
    ("save_round", "generate_question", "continue"),
    ("save_round", "final_review", "finish"),
    ("generate_hint", "format_output", "hint reply"),
    ("get_reference_answer", "format_output", "reference reply"),
    ("final_review", "format_output", "summary reply"),
    ("format_output", "END", "response returned"),
]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def center(box: tuple[int, int, int, int]) -> tuple[int, int]:
    x1, y1, x2, y2 = box
    return (x1 + x2) // 2, (y1 + y2) // 2


def edge_points(source: str, target: str) -> tuple[tuple[int, int], tuple[int, int]]:
    sx1, sy1, sx2, sy2, *_ = NODES[source]
    tx1, ty1, tx2, ty2, *_ = NODES[target]
    scx, scy = center((sx1, sy1, sx2, sy2))
    tcx, tcy = center((tx1, ty1, tx2, ty2))

    if abs(tcx - scx) > abs(tcy - scy):
        start = (sx2, scy) if tcx > scx else (sx1, scy)
        end = (tx1, tcy) if tcx > scx else (tx2, tcy)
    else:
        start = (scx, sy2) if tcy > scy else (scx, sy1)
        end = (tcx, ty1) if tcy > scy else (tcx, ty2)
    return start, end


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], label: str, font: ImageFont.ImageFont) -> None:
    draw.line([start, end], fill=LINE, width=3)
    ex, ey = end
    sx, sy = start
    if abs(ex - sx) > abs(ey - sy):
        direction = 1 if ex > sx else -1
        arrow = [(ex, ey), (ex - 14 * direction, ey - 8), (ex - 14 * direction, ey + 8)]
    else:
        direction = 1 if ey > sy else -1
        arrow = [(ex, ey), (ex - 8, ey - 14 * direction), (ex + 8, ey - 14 * direction)]
    draw.polygon(arrow, fill=LINE)

    lx = (sx + ex) // 2
    ly = (sy + ey) // 2
    bbox = draw.textbbox((0, 0), label, font=font)
    pad = 5
    draw.rounded_rectangle(
        [lx - (bbox[2] - bbox[0]) // 2 - pad, ly - 12, lx + (bbox[2] - bbox[0]) // 2 + pad, ly + 12],
        radius=8,
        fill=BACKGROUND,
        outline=(220, 203, 170),
    )
    draw.text((lx, ly), label, fill=MUTED, font=font, anchor="mm")


def draw_node(draw: ImageDraw.ImageDraw, data: tuple[int, int, int, int, str, str], title_font: ImageFont.ImageFont, subtitle_font: ImageFont.ImageFont) -> None:
    x1, y1, x2, y2, title, subtitle = data
    fill = TOOL if "tool" in subtitle else PANEL
    outline = ACCENT if title in {"agent_decision", "final_review"} else SAGE
    draw.rounded_rectangle([x1, y1, x2, y2], radius=24, fill=fill, outline=outline, width=4)
    draw.text(((x1 + x2) // 2, y1 + 35), title, fill=INK, font=title_font, anchor="mm")
    draw.text(((x1 + x2) // 2, y1 + 68), subtitle, fill=MUTED, font=subtitle_font, anchor="mm")


def render(output_path: Path) -> None:
    image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    title_font = load_font(42, bold=True)
    node_font = load_font(24, bold=True)
    subtitle_font = load_font(18)
    edge_font = load_font(14)

    draw.text((80, 55), "Interview Mentor LangGraph", fill=INK, font=title_font)
    draw.text((80, 110), "10 nodes, 18 edges, Ollama llama3.2:1b + local JSON tools", fill=MUTED, font=subtitle_font)

    for source, target, label in EDGES:
        draw_arrow(draw, *edge_points(source, target), label, edge_font)

    for node in NODES.values():
        draw_node(draw, node, node_font, subtitle_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG")


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("graph.png")
    render(destination)
    print(f"Graph PNG written to {destination}")

```

## tests/test_decision_router.py
```py
from app.graph.routers.decision_router import route_by_decision


def test_route_valid_action():
    assert route_by_decision({"pending_action": "generate_hint"}) == "generate_hint"


def test_route_invalid_action_fallback():
    assert route_by_decision({"pending_action": "dance"}) == "clarify"

```

## tests/test_evaluate_answer.py
```py
from app.schemas.evaluation import EvaluationResult


def test_evaluation_score_is_clamped():
    result = EvaluationResult(score=99, verdict="strong", feedback="ok", missing_points=[])
    assert result.score == 10


def test_evaluation_verdict_fallback():
    result = EvaluationResult(score=5, verdict="strange", feedback="ok", missing_points=[])
    assert result.verdict == "medium"

```

## tests/test_session_store.py
```py
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from app.storage.session_repository import SessionRepository


class DummySettings(BaseSettings):
    default_topic: str = "golang_backend"
    default_level: str = "junior"
    max_questions: int = 3
    sessions_dir: Path = Field(default_factory=Path)


def test_save_and_load_session(tmp_path):
    settings = DummySettings(sessions_dir=tmp_path)
    repo = SessionRepository(settings)  # type: ignore[arg-type]
    state = repo.reset_session(123, 456)
    state["current_question"] = "What is goroutine?"
    repo.save_session(123, state)

    loaded = repo.load_session(123, 456)
    assert loaded["user_id"] == 123
    assert loaded["chat_id"] == 456
    assert loaded["current_question"] == "What is goroutine?"

```

## tests/test_tools.py
```py
from app.tools.hint_tool import FALLBACK_HINT, generate_hint
from app.tools.reference_tool import FALLBACK_REFERENCE, get_reference_answer


def test_reference_answer_from_json():
    answer = get_reference_answer("golang_backend", "junior", "what_is_goroutine")
    assert "Goroutine" in answer


def test_reference_answer_fallback():
    answer = get_reference_answer("unknown", "junior", "missing")
    assert answer == FALLBACK_REFERENCE


def test_hint_from_json():
    hint = generate_hint("golang_backend", "junior", "what_is_channel")
    assert "goroutine" in hint.lower()


def test_hint_fallback():
    hint = generate_hint("unknown", "junior", "missing")
    assert hint == FALLBACK_HINT

```
