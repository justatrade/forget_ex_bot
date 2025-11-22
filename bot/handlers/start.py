from pathlib import Path
from datetime import datetime

from bot.utils.keyboards import get_start_keyboard_1, get_start_keyboard_2
from bot.utils.messages import (
    DARIA_CHANNEL,
    MARA_CHANNEL,
    START_MESSAGE_1,
    START_MESSAGE_2
)
from bot.utils.states import StartStates
from shared.config import setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import CameFrom, User, UserStatus

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, Message

from bot.services.came_from_service import CameFromService

logger = setup_logger(__name__)


async def start_handler(message: Message | CallbackQuery, bot: AsyncTeleBot):
    user = message.from_user
    came_from = CameFromService(bot)
    referal: CameFrom = await came_from.check_user(user.id)
    logger.info(f"User {user.id} started bot")

    async with DatabaseConnection.get_session() as session:
        session: AsyncSession

        result = await session.execute(
            select(User).filter(
                User.telegram_id == user.id
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
                came_from=referal,
            )
            session.add(db_user)
            logger.info(f"New user {user.id} created in database")

    message_text = START_MESSAGE_1.replace(
        "Дарья Фурман", f"<a href='{DARIA_CHANNEL}'>Дарья Фурман</a>"
    ).replace(
        "Мара Charmer", f"<a href='{MARA_CHANNEL}'>Мара Charmer</a>"
    )
    file_path = Path("./data/photo/start_photo.jpg")
    if file_path.exists():
        with open(file_path, "rb") as photo_file:
            await bot.send_photo(
                message.chat.id,
                photo=photo_file,
                caption=message_text,
                parse_mode="HTML",
                reply_markup=get_start_keyboard_1(),
            )
    else:
        await bot.send_message(
            message.chat.id,
            message_text,
            parse_mode="HTML",
            reply_markup=get_start_keyboard_1(),
            disable_web_page_preview=True,
        )

    await bot.set_state(user.id, StartStates.waiting_for_next, message.chat.id)

async def start_next_handler(call: CallbackQuery, bot: AsyncTeleBot):
    """Обработчик кнопки 'А что будет?'"""
    await bot.send_message(
        call.message.chat.id,
        START_MESSAGE_2,
        reply_markup=get_start_keyboard_2()
    )

    await bot.delete_state(call.from_user.id, call.message.chat.id)
    await bot.answer_callback_query(call.id)


def register_handlers(bot: AsyncTeleBot):
    bot.register_message_handler(
        lambda msg: start_handler(msg, bot),
        commands=['start'],
        pass_bot=True
    )

    bot.register_callback_query_handler(
        lambda call: start_next_handler(call, bot),
        func=lambda call: call.data == "start_next",
        pass_bot=True
    )
