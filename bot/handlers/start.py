from pathlib import Path
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    CallbackQuery,
    Message,
    User as TGUser,
)

from bot.utils.keyboards import (
    get_start_keyboard_1,
    get_start_keyboard_2,
    get_special_payment_keyboard
)
from bot.utils.messages import (
    DARIA_CHANNEL,
    MARA_CHANNEL,
    SPECIAL_CHOOSE_MESSAGE,
    SPECIAL_ALL_BOUGHT,
    START_MESSAGE_1,
    START_MESSAGE_2,
    START_SPECIAL_MESSAGE,
)
from bot.services import CameFromService, ChannelService
from shared.config import settings, setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import CameFrom, User, UserStatus


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
    user: TGUser = await starting_routine(message, bot)

    if settings.telegram.sell_mode == "Dasha-Mara":
        message_text = START_MESSAGE_1.replace(
            "Дарья Фурман", f"<a href='{DARIA_CHANNEL}'>Дарья Фурман</a>"
        ).replace(
            "Мара Charmer", f"<a href='{MARA_CHANNEL}'>Мара Charmer</a>"
        )
        file_path = Path("./data/photo/start_photo.jpg")
    elif settings.telegram.sell_mode == "Dasha":
        message_text = START_SPECIAL_MESSAGE.format(
            offer="http://dashafru.ru/%D0%9F%D1%83%D0%B1%D0%BB%D0%B8%D1%87%D0%BD%D0%B0%D1%8F-%D0%BE%D1%84%D0%B5%D1%80%D1%82%D0%B0/",
            privacy="http://dashafru.ru/%D0%9F%D0%BE%D0%BB%D0%B8%D1%82%D0%B8%D0%BA%D0%B0-%D0%BA%D0%BE%D0%BD%D1%84%D0%B8%D0%B4%D0%B5%D0%BD%D1%86%D0%B8%D0%B0%D0%BB%D1%8C%D0%BD%D0%BE%D1%81%D1%82%D0%B8/",
        )
        file_path = Path("./data/photo/start_special_photo.jpg")
    else:
        return

    await process_start(user, message_text, file_path, bot)


async def process_start(
        user: TGUser,
        message_text: str,
        file_path: Path | None,
        bot: AsyncTeleBot,
):
    if file_path.exists():
        with open(file_path, "rb") as photo_file:
            if len(message_text) > 1024:
                await bot.send_photo(
                    user.id,
                    photo=photo_file,
                    parse_mode="HTML",
                )
                await bot.send_message(
                    user.id,
                    message_text,
                    parse_mode="HTML",
                    reply_markup=get_start_keyboard_1(),
                    disable_web_page_preview=True,
                )
            else:
                await bot.send_photo(
                    user.id,
                    photo=photo_file,
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=get_start_keyboard_1(),
                )
    else:
        await bot.send_message(
            user.id,
            message_text,
            parse_mode="HTML",
            reply_markup=get_start_keyboard_1(),
            disable_web_page_preview=True,
        )


async def start_next_handler(call: CallbackQuery, bot: AsyncTeleBot):
    if settings.telegram.sell_mode == "Dasha-Mara":
        await bot.send_message(
            call.message.chat.id,
            START_MESSAGE_2,
            reply_markup=get_start_keyboard_2()
        )
    elif settings.telegram.sell_mode == "Dasha":
        user_id = call.message.chat.id

        user_presence = await ChannelService.check_user_presence(user_id)
        markup = await get_special_payment_keyboard(user_presence)
        if markup:
            await bot.send_message(
                user_id,
                text=SPECIAL_CHOOSE_MESSAGE,
                reply_markup=markup,
            )
        else:
            await bot.send_message(
                user_id,
                text=SPECIAL_ALL_BOUGHT,
            )

    await bot.answer_callback_query(call.id)


def register_handlers(bot: AsyncTeleBot):
    bot.register_message_handler(
        lambda msg: start_handler(msg, bot),
        commands=["start"],
        pass_bot=True,
        chat_types=["private"],
    )

    bot.register_callback_query_handler(
        lambda call: start_next_handler(call, bot),
        func=lambda call: call.data == "start_next",
        pass_bot=True,
    )
