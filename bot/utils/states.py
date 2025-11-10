from telebot.asyncio_handler_backends import State, StatesGroup


class PaymentStates(StatesGroup):
    waiting_for_promo = State()


class InsultStates(StatesGroup):
    waiting_for_gender = State()
