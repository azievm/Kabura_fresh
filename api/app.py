"""FastAPI-приложение Kabura Fresh Mini App.

Работает в одном процессе с ботом (см. main.py) и делит с ним базу.
Эндпоинты вынесены в routes.py; здесь — сборка приложения, CORS и страница.
"""
import logging
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.database import Database
from .routes import router

logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).parent / "webapp"


def create_api(db: Database) -> FastAPI:
    app = FastAPI(title="Kabura Fresh API", version="0.1.0")
    app.state.db = db

    # Mini App грузится с внешнего домена, поэтому нужен CORS.
    # TODO: сузить allow_origins до боевого домена фронтенда на проде.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/")
    async def index() -> FileResponse:
        """Страница Mini App (пока диагностическая; реальный UI — на этапе фронтенда)."""
        return FileResponse(WEBAPP_DIR / "index.html")

    @app.get("/api/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    return app
