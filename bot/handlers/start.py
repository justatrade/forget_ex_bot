from datetime import datetime
from typing import cast

from bot.utils.keyboards import get_start_keyboard
from bot.utils.messages import START_MESSAGE
from shared.config.logger import setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import User, UserStatus

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

logger = setup_logger(__name__)


async def start_handler(message: Message, bot: AsyncTeleBot):
    user = message.from_user
    logger.info(f"User {user.id} started bot")

    async with DatabaseConnection.get_session() as session:
        session: AsyncSession

        result = await session.execute(
            select(User).where(
                cast("ColumnElement[bool]", User.telegram_id == user.id)
            )
        )
        db_user = result.scalar_one_or_none()

        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                status=UserStatus.NEW,
                created_at=datetime.now(),
            )
            session.add(db_user)
            await session.commit()
            logger.info(f"New user {user.id} created in database")

    await bot.send_message(
        message.chat.id,
        START_MESSAGE,
        reply_markup=get_start_keyboard()
    )


def register_handlers(bot: AsyncTeleBot):
    bot.register_message_handler(
        lambda msg: start_handler(msg, bot),
        commands=['start'],
        pass_bot=True
    )
