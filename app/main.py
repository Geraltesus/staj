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
