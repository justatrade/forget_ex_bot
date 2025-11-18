from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from shared.config import settings


def get_start_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Хочу забыть бывшего", callback_data="payment_start")
    )
    keyboard.add(
        InlineKeyboardButton("Хочу узнать подробнее", url="https://example.com/longread")
    )
    keyboard.add(
        InlineKeyboardButton("Рандомное оскорбление бывшего", callback_data="insult_start")
    )
    return keyboard


def get_payment_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            f"Базовый курс - {settings.price.basic}₽",
            callback_data="payment_basic"
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            f"С ништяками - {settings.price.premium}₽",
            callback_data="payment_premium"
        )
    )
    keyboard.add(
        InlineKeyboardButton("Назад", callback_data="back_to_start")
    )
    return keyboard


# def get_promo_code_keyboard() -> InlineKeyboardMarkup:
#     keyboard = InlineKeyboardMarkup()
#     keyboard.add(
#         InlineKeyboardButton("Пропустить", callback_data="promo_skip")
#     )
#     return keyboard


def get_gender_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Мужчина", callback_data="gender_male")
    )
    keyboard.add(
        InlineKeyboardButton("Женщина", callback_data="gender_female")
    )
    return keyboard


def get_reminder_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Хочу забыть бывшего", callback_data="payment_start")
    )
    keyboard.add(
        InlineKeyboardButton("Рандомное оскорбление бывшего", callback_data="insult_start")
    )
    return keyboard


def get_payment_url_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("💳 Оплатить", url=payment_url)
    )
    return keyboard
