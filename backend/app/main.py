"""FastAPI entrypoint exposing a chat proxy for Azure OpenAI."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings, get_settings
from .llm import AzureOpenAIError, chat_completion
from .schemas import ChatMessage, ChatRequest, ChatResponse, UiTheme

logger = logging.getLogger("chat")

UI_SYSTEM_ADDENDUM = """
Always respond with valid JSON and nothing else, using this exact format:
{
  "reply": "<your response text>",
  "ui": {
    "background": "<hex color for page background that fits the mood/topic>",
    "accent": "<hex color for UI accents and user message bubbles>",
    "fontScale": <number between 0.9 and 1.2>
  }
}
"""

# The built frontend lives in ../frontend/dist relative to the backend/ package.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"


def create_app(frontend_dist: Path | None = FRONTEND_DIST) -> FastAPI:
    app = FastAPI(title="Trust-the-vibe-7 Chat API", version="0.1.0")

    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(
        req: ChatRequest,
        settings: Settings = Depends(get_settings),
    ) -> ChatResponse:
        # Inject UI JSON instructions into the system message
        messages = list(req.messages)
        for i, msg in enumerate(messages):
            if msg.role == "system":
                messages[i] = ChatMessage(
                    role="system",
                    content=msg.content + "\n\n" + UI_SYSTEM_ADDENDUM,
                )
                break
        else:
            messages.insert(0, ChatMessage(role="system", content=UI_SYSTEM_ADDENDUM))

        try:
            data = await chat_completion(
                settings,
                messages,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )
        except AzureOpenAIError as exc:
            logger.warning("azure openai failed: %s", exc)
            raise HTTPException(status_code=502, detail=exc.detail) from exc

        choices = data.get("choices") or []
        if not choices:
            raise HTTPException(status_code=502, detail="empty response from model")
        raw = (choices[0].get("message") or {}).get("content", "")

        ui: UiTheme | None = None
        try:
            parsed = json.loads(raw)
            reply = parsed.get("reply", raw)
            if isinstance(parsed.get("ui"), dict):
                ui = UiTheme(**parsed["ui"])
        except (json.JSONDecodeError, ValueError, TypeError):
            reply = raw

        return ChatResponse(
            reply=reply,
            model=data.get("model", settings.azure_openai_deployment),
            usage=data.get("usage"),
            ui=ui,
        )

    _mount_frontend(app, frontend_dist)
    return app


def _mount_frontend(app: FastAPI, dist: Path | None) -> None:
    """Serve the built SPA from `dist` if present; otherwise show a helpful stub."""
    index = dist / "index.html" if dist else None

    if not dist or not index or not index.exists():
        logger.info("frontend dist not found at %s — skipping static mount", dist)

        @app.get("/", include_in_schema=False)
        def _missing_frontend() -> dict[str, str]:
            return {
                "status": "ok",
                "message": (
                    "Frontend not built yet. Run `npm run build` in frontend/ "
                    "to have the backend serve the UI from /."
                ),
            }

        return

    # Static assets (hashed filenames under /assets/*).
    assets_dir = dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # SPA fallback: every non-API GET returns index.html so client-side routing works.
    @app.get("/{full_path:path}", include_in_schema=False)
    def _spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)

        candidate = (dist / full_path).resolve()
        # Prevent path traversal and only serve files that actually live under dist.
        try:
            candidate.relative_to(dist.resolve())
        except ValueError:
            return FileResponse(index)

        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
