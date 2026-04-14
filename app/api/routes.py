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
