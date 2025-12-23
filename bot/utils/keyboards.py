from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from shared.config import settings
from shared.schemas import DashaChannelPresence


def get_start_keyboard_1() -> InlineKeyboardMarkup:
    """Первая клавиатура - после приветствия"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("А что будет?", callback_data="start_next")
    )
    return keyboard


def get_start_keyboard_2() -> InlineKeyboardMarkup:
    """Вторая клавиатура - после описания курса"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Хочу забыть бывшего", callback_data="payment_start")
    )
    # keyboard.add(
    #     InlineKeyboardButton("Хочу узнать подробнее", url="https://dashafru.ru")
    # )
    # keyboard.add(
    #     InlineKeyboardButton("Рандомное оскорбление бывшего", callback_data="insult_start")
    # )
    return keyboard


def get_course_payment_keyboard() -> InlineKeyboardMarkup:
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


async def get_special_payment_keyboard(
        user_presence: DashaChannelPresence
) -> InlineKeyboardMarkup | None:
    pay_via_rk_val = InlineKeyboardButton(
        text="Оплатить Valentine Special ❤", callback_data="pay_via_rk_val"
    )
    pay_via_rk_ny = InlineKeyboardButton(
        text="Оплатить New Year Special 🎄", callback_data="pay_via_rk_ny"
    )
    pay_via_rk_12 = InlineKeyboardButton(
        text="Оплатить 8ой Сезон 👯‍♀", callback_data="pay_via_rk_12"
    )
    pay_via_rk_all = InlineKeyboardButton(
        text="Все сезоны -25% 👯‍♀", callback_data="pay_via_rk_all"
    )
    markup = InlineKeyboardMarkup()
    if user_presence.all_special:
        return None

    if not user_presence.ny_special:
        markup.add(pay_via_rk_ny)

    if not user_presence.feb_special:
        markup.add(pay_via_rk_val)

    if not user_presence.twelve_special:
        markup.add(pay_via_rk_12)

    if not user_presence.any_special:
        markup.add(pay_via_rk_all)

    return markup


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
