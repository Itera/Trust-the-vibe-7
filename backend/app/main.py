"""FastAPI entrypoint for HuMotivatoren."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings, get_settings
from .llm import AzureOpenAIError
from .orchestrator import motivate
from .personas import PERSONAS
from .schemas import MotivationPackage, MotivationRequest, PersonaSummary

logger = logging.getLogger("humotivatoren")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"


def create_app(frontend_dist: Path | None = FRONTEND_DIST) -> FastAPI:
    app = FastAPI(title="HuMotivatoren API", version="0.2.0")

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

    @app.get("/api/personas", response_model=list[PersonaSummary])
    def personas(language: str = "en") -> list[PersonaSummary]:
        lang = "no" if language == "no" else "en"
        return [
            PersonaSummary(
                key=p.key,
                name=p.name,
                tagline=p.tagline(lang),  # type: ignore[arg-type]
                accent_color=p.accent_color,
            )
            for p in PERSONAS.values()
        ]

    @app.post("/api/motivate", response_model=MotivationPackage)
    async def motivate_endpoint(
        req: MotivationRequest,
        settings: Settings = Depends(get_settings),
    ) -> MotivationPackage:
        try:
            return await motivate(settings, req)
        except AzureOpenAIError as exc:
            logger.warning("motivate upstream failed: %s", exc)
            raise HTTPException(status_code=502, detail=exc.detail) from exc

    _mount_frontend(app, frontend_dist)
    return app


def _mount_frontend(app: FastAPI, dist: Path | None) -> None:
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

    assets_dir = dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def _spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)

        candidate = (dist / full_path).resolve()
        try:
            candidate.relative_to(dist.resolve())
        except ValueError:
            return FileResponse(index)

        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
