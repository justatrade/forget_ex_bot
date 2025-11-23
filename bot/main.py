import asyncio
import time

from redis.asyncio import Redis
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateRedisStorage

from bot.handlers import start, payment#, insults, common
from bot.services import ChannelService
# from bot.scheduler.reminders import start_scheduler
from shared.config import setup_logger
from shared.config import settings
from shared.database.connection import DatabaseConnection
from shared.services import RedisStreamConsumer


logger = setup_logger(__name__)

redis_client = Redis(
    host=settings.redis.host,
    port=settings.redis.port,
    db=settings.redis.db,
    password=settings.redis.password,
    decode_responses=True,
)

state_storage = StateRedisStorage(
    host=settings.redis.host,
    port=settings.redis.port,
    db=settings.redis.db,
    password=settings.redis.password,
)
bot = AsyncTeleBot(settings.telegram.bot_token, state_storage=state_storage)
redis_consumer: RedisStreamConsumer | None = None


async def check_redis():
    try:
        await redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise


async def on_startup():
    global redis_consumer
    logger.info("Bot starting...")
    await check_redis()
    await DatabaseConnection.create_tables()
    ChannelService.set_bot(bot)
    logger.debug(f"ChannelService._bot is {ChannelService._bot}")
    redis_consumer = RedisStreamConsumer(
        redis_client,
        settings.redis.stream_name,
        settings.redis.group_name,
        settings.redis.consumer_name,
        settings.redis.block_ms,
        settings.redis.read_count,
    )
    redis_consumer.run_in_background()
    # start_scheduler(bot)
    logger.info("Bot started successfully")


async def on_shutdown():
    logger.info("Bot shutting down...")
    if redis_consumer is not None:
        try:
            await redis_consumer.stop()
            logger.info("RedisStreamConsumer stopped")
        except Exception as e:
            logger.exception(f"Error stopping RedisStreamConsumer: {e}")
    await DatabaseConnection.close()
    await redis_client.close()
    logger.info("Bot stopped")


async def main():
    await on_startup()

    start.register_handlers(bot)
    payment.register_handlers(bot)
    # insults.register_handlers(bot)
    # common.register_handlers(bot)
    while True:
        try:
            await bot.polling(timeout=20)
        except Exception as e:
            time.sleep(1)
            logger.error(f"Bot polling error: {e}")
        finally:
            break

    await on_shutdown()


if __name__ == "__main__":
    # if settings.app.debug:
    #     import pydevd_pycharm
    #
    #     pydevd_pycharm.settrace(
    #         host="host.docker.internal",
    #         port=5678,
    #         stdoutToServer=True,
    #         stderrToServer=True,
    #         suspend=False,
    #     )
    asyncio.run(main())
