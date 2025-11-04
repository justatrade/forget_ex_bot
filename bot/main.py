import asyncio
from telebot.async_telebot import AsyncTeleBot

from bot.handlers import start #, payment, insults, common
# from bot.scheduler.reminders import start_scheduler
from shared.config.logger import setup_logger
from shared.config.settings import settings
from shared.database.connection import DatabaseConnection


logger = setup_logger(__name__)

bot = AsyncTeleBot(settings.telegram.bot_token)


async def on_startup():
    logger.info("Bot starting...")
    await DatabaseConnection.create_tables()
    # start_scheduler(bot)
    logger.info("Bot started successfully")


async def on_shutdown():
    logger.info("Bot shutting down...")
    await DatabaseConnection.close()
    logger.info("Bot stopped")


async def main():
    await on_startup()

    start.register_handlers(bot)
    # payment.register_handlers(bot)
    # insults.register_handlers(bot)
    # common.register_handlers(bot)

    try:
        await bot.infinity_polling(timeout=5)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
    finally:
        await on_shutdown()


if __name__ == "__main__":
    asyncio.run(main())