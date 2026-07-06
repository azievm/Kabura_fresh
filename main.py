import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from app.config import BOT_TOKEN
from app.database import Database
from app.fsm_storage import SQLiteFSMStorage
from app.handlers import router
from app.admin_handlers import admin
from app.middlewares import DBSessionMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=BOT_TOKEN)
    db = Database()
    dp = Dispatcher(storage=SQLiteFSMStorage(db.async_session))

    max_retries = 5
    retry_delay = 5

    try:
        await db.init()
        dp.include_router(router)
        dp.include_router(admin)
        dp["db"] = db
        dp.message.middleware(DBSessionMiddleware(db.async_session))
        dp.callback_query.middleware(DBSessionMiddleware(db.async_session))

        for attempt in range(max_retries):
            try:
                logger.info("Подключение к Telegram (попытка %d/%d)...", attempt + 1, max_retries)
                await dp.start_polling(bot)
                break
            except TelegramNetworkError as e:
                logger.warning("Ошибка подключения: %s", e)
                if attempt < max_retries - 1:
                    logger.info("Переподключение через %d секунд...", retry_delay)
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Не удалось подключиться после %d попыток.", max_retries)
                    raise

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
