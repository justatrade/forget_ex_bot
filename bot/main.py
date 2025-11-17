import asyncio

from redis.asyncio import Redis
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateRedisStorage

from bot.handlers import start, payment#, insults, common
from bot.services import ChannelService
# from bot.scheduler.reminders import start_scheduler
from shared.config.logger import setup_logger
from shared.config.settings import settings
from shared.database.connection import DatabaseConnection


logger = setup_logger(__name__)

redis_client = Redis(
    host=settings.redis.host,
    port=settings.redis.port,
    db=settings.redis.db,
    decode_responses=True,
)

state_storage = StateRedisStorage(
    host=settings.redis.host,
    port=settings.redis.port,
    db=settings.redis.db,
)
bot = AsyncTeleBot(settings.telegram.bot_token, state_storage=state_storage)


async def check_redis():
    try:
        await redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise


async def on_startup():
    logger.info("Bot starting...")
    await check_redis()
    await DatabaseConnection.create_tables()
    ChannelService.set_bot(bot)
    # start_scheduler(bot)
    logger.info("Bot started successfully")


async def on_shutdown():
    logger.info("Bot shutting down...")
    await DatabaseConnection.close()
    await redis_client.close()
    logger.info("Bot stopped")


async def main():
    await on_startup()

    start.register_handlers(bot)
    payment.register_handlers(bot)
    # insults.register_handlers(bot)
    # common.register_handlers(bot)

    try:
        await bot.infinity_polling(timeout=60)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    if settings.app.debug:
        import pydevd_pycharm

        pydevd_pycharm.settrace(
            host="host.docker.internal",
            port=5678,
            stdoutToServer=True,
            stderrToServer=True,
            suspend=False,
        )
    asyncio.run(main())
