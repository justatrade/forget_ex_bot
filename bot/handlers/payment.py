from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery

from bot.utils.keyboards import (
    get_payment_keyboard,
    get_payment_url_keyboard,
    get_start_keyboard_1
)
from bot.utils.messages import PAYMENT_MESSAGE
from shared.config import setup_logger
from shared.config import settings
from shared.database.connection import DatabaseConnection
from shared.database.models import User, UserStatus
from shared.services import ProdamusService


logger = setup_logger(__name__)


async def payment_start_handler(call: CallbackQuery, bot: AsyncTeleBot):
    await bot.send_message(
        call.message.chat.id,
        PAYMENT_MESSAGE.format(
            price_basic=settings.price.basic,
            price_premium=settings.price.premium
        ),
        reply_markup=get_payment_keyboard()
    )

    async with DatabaseConnection.get_session() as session:
        session: AsyncSession
        result = await session.execute(
            select(User)
            .options(selectinload(User.payments))
            .filter(
                User.telegram_id == call.from_user.id,
            )
        )
        user = result.scalar_one_or_none()
        if user:
            user.status = UserStatus.INTERESTED


async def payment_basic_handler(call: CallbackQuery, bot: AsyncTeleBot):
    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data["package"] = "basic"
        data["price"] = settings.price.basic

    user_id = call.from_user.id

    await create_payment(user_id, bot)


async def payment_premium_handler(call: CallbackQuery, bot: AsyncTeleBot):
    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data["package"] = "premium"
        data["price"] = settings.price.premium

    user_id = call.from_user.id

    await create_payment(user_id, bot)


async def create_payment(user_id: int, bot: AsyncTeleBot):
    async with (bot.retrieve_data(user_id) as data):
        price = data.get("price")
        if not price:
            price = (
                settings.price.basic
                if data.get("package") == "basic"
                else settings.price.premium
            )

    if not price:
        return

    final_price = price

    payment_url = await ProdamusService.create_payment(
        user_id=user_id,
        amount=final_price,
    )

    async with DatabaseConnection.get_session() as session:
        session: AsyncSession
        result = await session.execute(
            select(User)
            .options(selectinload(User.payments))
            .filter(
                User.telegram_id == user_id)
            )
        user = result.scalar_one_or_none()
        if user:
            user.status = UserStatus.PENDING_PAYMENT
            await session.flush()
            await session.commit()

    await bot.send_message(
        user_id,
        text=f"Сумма к оплате: {final_price}₽\n\n"
             f"Нажми на кнопку для перехода к оплате:",
        reply_markup=get_payment_url_keyboard(payment_url)
    )

    await bot.delete_state(user_id)


async def back_to_start_handler(call: CallbackQuery, bot: AsyncTeleBot):
    from bot.utils.messages import START_MESSAGE
    await bot.send_message(
        call.message.chat.id,
        START_MESSAGE,
        reply_markup=get_start_keyboard_1()
    )


def register_handlers(bot: AsyncTeleBot):
    bot.register_callback_query_handler(
        lambda call: payment_start_handler(call, bot),
        func=lambda call: call.data == "payment_start",
        pass_bot=True
    )
    bot.register_callback_query_handler(
        lambda call: payment_basic_handler(call, bot),
        func=lambda call: call.data == "payment_basic",
        pass_bot=True
    )
    bot.register_callback_query_handler(
        lambda call: payment_premium_handler(call, bot),
        func=lambda call: call.data == "payment_premium",
        pass_bot=True
    )
    bot.register_callback_query_handler(
        lambda call: back_to_start_handler(call, bot),
        func=lambda call: call.data == "back_to_start",
        pass_bot=True
    )