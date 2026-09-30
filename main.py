import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from app.config import BOT_TOKEN, API_HOST, API_PORT
from app.database import Database
from app.fsm_storage import SQLiteFSMStorage
from app.handlers import router
from app.admin_handlers import admin
from app.maintenance import cleanup_loop
from app.middlewares import DBSessionMiddleware
from api import create_api

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

async def run_polling(dp: Dispatcher, bot: Bot):
    """Поллинг Telegram с повторными попытками при сетевых сбоях."""
    max_retries = 5
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            logger.info("Подключение к Telegram (попытка %d/%d)...", attempt + 1, max_retries)
            await dp.start_polling(bot)
            return
        except TelegramNetworkError as e:
            logger.warning("Ошибка подключения: %s", e)
            if attempt < max_retries - 1:
                logger.info("Переподключение через %d секунд...", retry_delay)
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Не удалось подключиться после %d попыток.", max_retries)
                raise

async def main():
    bot = Bot(token=BOT_TOKEN)
    db = Database()
    dp = Dispatcher(storage=SQLiteFSMStorage(db.async_session))

    try:
        await db.init()
        dp.include_router(router)
        dp.include_router(admin)
        dp["db"] = db
        dp.message.middleware(DBSessionMiddleware(db.async_session))
        dp.callback_query.middleware(DBSessionMiddleware(db.async_session))

        # HTTP API для Mini App — в том же процессе и на той же базе, что и бот
        api = create_api(db, bot=bot)
        server = uvicorn.Server(
            uvicorn.Config(api, host=API_HOST, port=API_PORT, log_level="info")
        )
        logger.info("Запуск HTTP API на %s:%d", API_HOST, API_PORT)

        await asyncio.gather(
            run_polling(dp, bot),
            server.serve(),
            cleanup_loop(db),
        )

    except Exception:
        logger.exception("Бот аварийно остановлен")
        raise
    finally:
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n✋ Бот остановлен.")
