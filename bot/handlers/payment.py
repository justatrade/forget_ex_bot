from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, Message
from telebot.asyncio_filters import StateFilter
from shared.config.logger import setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import User, UserStatus
from bot.utils.keyboards import (
    get_payment_keyboard,
    get_promo_code_keyboard,
    get_payment_url_keyboard,
    get_start_keyboard
)
from bot.utils.messages import (
    PAYMENT_MESSAGE,
    PROMO_CODE_PROMPT,
    PROMO_CODE_INVALID,
    PROMO_CODE_APPLIED
)
from bot.utils.states import PaymentStates
from bot.services.promo_code_service import PromoCodeService
from bot.services.prodamus import ProdamusService
from shared.config.settings import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast

logger = setup_logger(__name__)


async def payment_start_handler(call: CallbackQuery, bot: AsyncTeleBot):
    await bot.edit_message_text(
        PAYMENT_MESSAGE.format(
            price_basic=settings.price.price_basic,
            price_premium=settings.price.price_premium
        ),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=get_payment_keyboard()
    )

    async with DatabaseConnection.get_session() as session:
        session: AsyncSession
        result = await session.execute(
            select(User).where(
                cast(
                    "ColumnElement[bool]",
                    User.telegram_id == call.from_user.id,
                )
            )
        )
        user = result.scalar_one_or_none()
        if user:
            user.status = UserStatus.INTERESTED


async def payment_basic_handler(call: CallbackQuery, bot: AsyncTeleBot):
    await bot.set_state(call.from_user.id, PaymentStates.waiting_for_promo, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data["package"] = "basic"
        data['price'] = settings.price.price_basic

    await bot.edit_message_text(
        PROMO_CODE_PROMPT,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=get_promo_code_keyboard()
    )


async def payment_premium_handler(call: CallbackQuery, bot: AsyncTeleBot):
    await bot.set_state(call.from_user.id, PaymentStates.waiting_for_promo, call.message.chat.id)

    async with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        data['package'] = 'premium'
        data['price'] = settings.price.price_premium

    await bot.edit_message_text(
        PROMO_CODE_PROMPT,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=get_promo_code_keyboard()
    )


async def promo_skip_handler(call: CallbackQuery, bot: AsyncTeleBot):
    await create_payment(call.from_user.id, call.message.chat.id, bot, promo_code=None)


async def promo_code_handler(message: Message, bot: AsyncTeleBot):
    promo_code = message.text.strip()
    user_id = message.from_user.id

    async with DatabaseConnection.get_session() as session:
        is_valid = await PromoCodeService.validate_promo_code(session, promo_code)

        if is_valid:
            discount = await PromoCodeService.get_discount(session, promo_code)
            await bot.send_message(
                message.chat.id,
                PROMO_CODE_APPLIED.format(discount=discount)
            )
            await create_payment(user_id, message.chat.id, bot, promo_code=promo_code)
        else:
            await bot.send_message(message.chat.id, PROMO_CODE_INVALID)
            await create_payment(user_id, message.chat.id, bot, promo_code=None)


async def create_payment(user_id: int, chat_id: int, bot: AsyncTeleBot, promo_code: str | None):
    async with bot.retrieve_data(user_id, chat_id) as data:
        price = data.get('price')

    if not price:
        return

    final_price = price

    if promo_code:
        async with DatabaseConnection.get_session() as session:
            final_price = await PromoCodeService.calculate_final_price(session, promo_code, final_price)

    payment_url = await ProdamusService.create_payment(
        user_id=user_id,
        amount=final_price,
        promo_code=promo_code
    )

    async with DatabaseConnection.get_session() as session:
        session: AsyncSession
        result = await session.execute(
            select(User).where(
                cast("ColumnElement[bool]", User.telegram_id == user_id)
            )
        )
        user = result.scalar_one_or_none()
        if user:
            user.status = UserStatus.PENDING_PAYMENT

    await bot.send_message(
        chat_id,
        text=f"Сумма к оплате: {final_price}₽\n\n"
             f"Нажми на кнопку для перехода к оплате:",
        reply_markup=get_payment_url_keyboard(payment_url)
    )

    await bot.delete_state(user_id, chat_id)


async def back_to_start_handler(call: CallbackQuery, bot: AsyncTeleBot):
    from bot.utils.messages import START_MESSAGE
    await bot.edit_message_text(
        START_MESSAGE,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=get_start_keyboard()
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
        lambda call: promo_skip_handler(call, bot),
        func=lambda call: call.data == "promo_skip",
        pass_bot=True
    )
    bot.register_message_handler(
        lambda msg: promo_code_handler(msg, bot),
        state=PaymentStates.waiting_for_promo,
        pass_bot=True
    )
    bot.register_callback_query_handler(
        lambda call: back_to_start_handler(call, bot),
        func=lambda call: call.data == "back_to_start",
        pass_bot=True
    )