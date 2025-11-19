from telebot.asyncio_handler_backends import State, StatesGroup


class StartStates(StatesGroup):
    waiting_for_next = State()


class InsultStates(StatesGroup):
    waiting_for_gender = State()
