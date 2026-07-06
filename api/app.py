"""FastAPI-приложение Kabura Fresh Mini App.

Работает в одном процессе с ботом (см. main.py) и делит с ним базу.
Пока содержит только каркас и эндпоинт /api/me для проверки авторизации.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Database, User
from .deps import get_session, get_telegram_user

logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).parent / "webapp"


class MeResponse(BaseModel):
    telegram_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    delivery_address: Optional[str] = None


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

    @app.get("/")
    async def index() -> FileResponse:
        """Страница Mini App (пока диагностическая; реальный UI — на этапе фронтенда)."""
        return FileResponse(WEBAPP_DIR / "index.html")

    @app.get("/api/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/me", response_model=MeResponse)
    async def me(
        tg_user: Dict[str, Any] = Depends(get_telegram_user),
        session: AsyncSession = Depends(get_session),
    ) -> MeResponse:
        """Возвращает профиль текущего пользователя, создавая запись при первом заходе."""
        telegram_id = int(tg_user["id"])
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))

        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=tg_user.get("username"),
                first_name=tg_user.get("first_name"),
                last_name=tg_user.get("last_name"),
            )
            session.add(user)
            await session.commit()
            logger.info("Mini App: создан новый пользователь telegram_id=%s", telegram_id)

        return MeResponse(
            telegram_id=user.telegram_id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            customer_name=user.customer_name,
            phone=user.phone,
            delivery_address=user.delivery_address,
        )

    return app
