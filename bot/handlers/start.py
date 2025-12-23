from pathlib import Path
from datetime import datetime

from bot.utils.keyboards import (
    get_start_keyboard_1,
    get_start_keyboard_2,
    get_special_payment_keyboard
)
from bot.utils.messages import (
    DARIA_CHANNEL,
    MARA_CHANNEL,
    START_MESSAGE_1,
    START_MESSAGE_2
)
from bot.utils.states import StartStates
from bot.services import ChannelService
from shared.config import settings, setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import CameFrom, User, UserStatus

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User as TGUser,
)

from bot.services.came_from_service import CameFromService

logger = setup_logger(__name__)


async def starting_routine(message: Message, bot: AsyncTeleBot) -> TGUser:
    user = message.from_user
    came_from = CameFromService(bot)
    referral: CameFrom = await came_from.check_user(user.id)
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
                came_from=referral,
            )
            session.add(db_user)
            logger.info(f"New user {user.id} created in database")
        else:
            if db_user.telegram_id in settings.telegram.admin_id:
                db_user.came_from = referral

        return user


async def start_handler(message: Message | CallbackQuery, bot: AsyncTeleBot):
    user = await starting_routine(message, bot)

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


async def start_special_handler(message: Message | CallbackQuery, bot: AsyncTeleBot):
    await starting_routine(message, bot)

    user_presence = await ChannelService.check_user_presence(message.chat.id)
    markup = await get_special_payment_keyboard(user_presence)
    if markup:
        await bot.send_message(
            message.chat.id,
            text="Привет, пирожок!\nВыбирай развлечение на месяц 👌🏻",
            reply_markup=markup,
        )
    else:
        await bot.send_message(
            message.chat.id,
            text="Пирожок, ну ты просто молодец! "
                 "Пока больше нечего купить, но можешь закинуть 💵 просто так..."
        )


def register_handlers(bot: AsyncTeleBot):
    if settings.telegram.sell_mode == "Dasha-Mara":
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
    elif settings.telegram.sell_mode == "Dasha":
        bot.register_message_handler(
            lambda msg: start_special_handler(msg, bot),
            commands=["start"],
            pass_bot=True,
        )
    else:
        pass
