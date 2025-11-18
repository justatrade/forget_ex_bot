from telebot.asyncio_handler_backends import State, StatesGroup


class InsultStates(StatesGroup):
    waiting_for_gender = State()
