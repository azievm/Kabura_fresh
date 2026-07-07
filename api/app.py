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
from fastapi.staticfiles import StaticFiles

from app.database import Database
from .routes import router

logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).parent / "webapp"                       # диагностическая страница (fallback)
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"  # собранный Mini App


def create_api(db: Database, bot=None) -> FastAPI:
    app = FastAPI(title="Kabura Fresh API", version="0.1.0")
    app.state.db = db
    app.state.bot = bot  # для уведомлений админов о новых заказах

    # Mini App грузится с внешнего домена, поэтому нужен CORS.
    # TODO: сузить allow_origins до боевого домена фронтенда на проде.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/api/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    # Раздаём собранный фронтенд (Vite build). Если сборки нет — диагностическая страница.
    if FRONTEND_DIST.exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(FRONTEND_DIST / "index.html")
    else:
        @app.get("/")
        async def index() -> FileResponse:
            logger.warning("frontend/dist не найден — отдаю диагностическую страницу")
            return FileResponse(WEBAPP_DIR / "index.html")

    return app
