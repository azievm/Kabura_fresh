"""Фоновое обслуживание базы."""
import asyncio
import logging
from datetime import timedelta

from sqlalchemy import delete, select

from .database import Database, Order, OrderItem, utc_now

logger = logging.getLogger(__name__)

# Заказ Mini App создаётся со статусом 'pending' до оплаты. Ссылка YooKassa живёт
# недолго, поэтому неоплаченные заказы старше суток можно безопасно удалять.
PENDING_TTL = timedelta(hours=24)
CLEANUP_INTERVAL_SECONDS = 3600


async def cleanup_pending_orders(db: Database) -> int:
    cutoff = utc_now() - PENDING_TTL
    async with db.async_session() as session:
        ids = (await session.scalars(
            select(Order.id).where(Order.status == "pending", Order.created_at < cutoff)
        )).all()
        if not ids:
            return 0
        await session.execute(delete(OrderItem).where(OrderItem.order_id.in_(ids)))
        await session.execute(delete(Order).where(Order.id.in_(ids)))
        await session.commit()
        return len(ids)


async def cleanup_loop(db: Database) -> None:
    while True:
        try:
            removed = await cleanup_pending_orders(db)
            if removed:
                logger.info("Удалено неоплаченных заказов старше суток: %d", removed)
        except Exception:
            logger.exception("Ошибка очистки неоплаченных заказов")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
