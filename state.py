from aiogram.dispatcher.filters.state import State, StatesGroup

class Accounts(StatesGroup):
    accountId = State()
    CaptchaId = State()
    auth = State()
    delete = State()
    captcha = State()