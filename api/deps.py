"""FastAPI-зависимости: доступ к БД и аутентификация по Telegram initData."""
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Database
from .security import InitDataError, parse_user, validate_init_data


async def get_db(request: Request) -> Database:
    return request.app.state.db


async def get_session(db: Database = Depends(get_db)) -> AsyncSession:
    async with db.async_session() as session:
        yield session


def _extract_init_data(
    authorization: Optional[str],
    x_telegram_init_data: Optional[str],
) -> str:
    """initData принимается либо как `Authorization: tma <initData>`
    (стандарт @telegram-apps SDK), либо как заголовок X-Telegram-Init-Data."""
    if authorization and authorization.startswith("tma "):
        return authorization[len("tma "):]
    if x_telegram_init_data:
        return x_telegram_init_data
    raise HTTPException(status_code=401, detail="missing initData")


async def get_telegram_user(
    authorization: Optional[str] = Header(default=None),
    x_telegram_init_data: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """Проверяет подпись initData и возвращает объект пользователя Telegram."""
    raw = _extract_init_data(authorization, x_telegram_init_data)
    try:
        fields = validate_init_data(raw)
        return parse_user(fields)
    except InitDataError as e:
        raise HTTPException(status_code=401, detail=f"invalid initData: {e}")
