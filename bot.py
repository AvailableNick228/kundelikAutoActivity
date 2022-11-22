import asyncio
from time import sleep
from datetime import datetime

from aiogram.utils import executor
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram import types
from aiogram.dispatcher.filters import Filter

import config
from state import *
import kb
from models import Person, Account, session

storage = MemoryStorage()
bot = Bot(config.bot_token, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot, storage=storage)

class isAdmin(Filter):
    key = "is_admin"

    async def check(self, message: Message):
        user = session.query(Person).filter_by(chatId=message.chat.id).first()
        return user.role == 'admin'


class UserFilter(Filter):
    key = "user_filter"

    async def check(self, message: Message):
        user = session.query(Person).filter_by(chatId=message.chat.id).first()
        if user is None:
            newPerson = Person(
                name= message.chat.full_name,
                chatId= message.chat.id
            )

            session.add(newPerson)   
            session.commit()
            await message.reply(f"❌ У вас нету доступа ❌\n🆔 Ваш айди: `{message.chat.id}`")
            return False

        elif user.role == 'notUser':

            await message.reply(f"❌ У вас нету доступа ❌\n🆔 Ваш айди: `{message.chat.id}`")
            return False
        else:
            return True




@dp.message_handler(UserFilter(), commands=['start'])
async def startCommand(message: Message):
    await message.answer(f"👋 Привет *{message.chat.full_name}*\n\n🤖 _Бот разработан чтобы каждый день проявляет активность с аккаунтов которые вы добавили активность чтобы апай не ругалась_\n👨‍💻 Разработано *Бакбергеном*\n", reply_markup=kb.startMenu)


@dp.message_handler(UserFilter(), text='💼 Аккаунты')
async def accounts(message: Message):
    messageText = "💼 Аккаунты\nФормат: Айди, Логин, Дата добавления\n\n"
    accounts = session.query(Account).filter_by(user_id=message.chat.id).all()
    for account in accounts:
        messageText += f'{account.id} | {account.login} | {datetime.strftime(account.created_on, "%m.%d.%Y %H:%M:%S")}\n'
    messageText += '\nВыберите действие 👇'
    await message.answer(messageText, reply_markup=kb.accountsButtons, parse_mode=types.ParseMode.HTML)


@dp.message_handler(UserFilter(), text='➕ Добавить')
async def addAccount(message: Message):
    await message.bot.delete_message(message.chat.id, message.message_id)
    await message.answer('✍️ Напишите данные аккаунта в формате (login:password) без скобок')
    await Accounts.auth.set()


@dp.message_handler(UserFilter(), state=Accounts.auth)
async def accountsAuth(message: Message, state: FSMContext):
    if len(message.text.split(':')) != 2:
        await message.answer('❌ Не правильный логин или пароль!')
    else:
        login = message.text.split(':')[0]
        password = message.text.split(':')[1]

        account = session.query(Account).filter_by(login=login).first()
        if account:
            await message.answer('❌ Аккаунт уже существует в базе данных!')
        else:
            newAccount = Account(
                login=login,
                password=password,
                user_id=message.chat.id
            )
            
            await message.answer('⏳ Пытаюсь ввойти в аккаунт...')
            auth = newAccount.auth()
            
            if auth['success'] == False:
                await message.answer(auth['message'])
            else:
                await message.answer(auth['message'])
                session.add(newAccount)   
                session.commit()

            if auth is False:
                session.add(newAccount)   
                session.commit()
                await state.set_state(Accounts.captcha)
                await state.update_data(accountId=newAccount.id)
                await state.update_data(accountId=auth['CaptchaImage'])
                await message.answer(f'🆗 Для авторизация нужно решить <a href="{auth["CaptchaImage"]}">капчу</a>', parse_mode='HTML')
                


@dp.message_handler(UserFilter(), state=Accounts.captcha)
async def accountsCaptcha(message: Message, state: FSMContext):
    user_data = await state.get_data()
    account = session.query(Account).filter_by(id=user_data['accountId']).first()
    await message.answer('⏳ Пытаюсь ввойти в аккаунт...')
    account.auth()
     

@dp.message_handler(UserFilter(), text='🔙 Назад', state='*')
async def backButton(message: Message, state: FSMContext):
    await state.finish()
    return await startCommand(message)


@dp.message_handler(UserFilter(), text='➖ Удалить')
async def deleteAccount(message: Message, state: FSMContext):
    await message.answer('Введите айди аккаунта который хотите удалить')
    await state.set_state(Accounts.delete)


@dp.message_handler(UserFilter(), state=Accounts.delete)
async def deleteAccountState(message: Message, state: FSMContext):    
    id = message.text
    account = session.query(Account).filter_by(id=id, user_id=message.chat.id).first()
    if account is not None:
        session.delete(account)
        session.commit()
        await state.finish()
        await message.answer("✅ Аккаунт удалён!", reply_markup=kb.startMenu)
    else:
        await message.answer('❌ Аккаунт не найден! Попробуйте снова', reply_markup=kb.startMenu)


@dp.message_handler(isAdmin(), commands=['setRole'])
async def setRole(message: Message):
    if len(message.text.split(' ')) != 3:
        await message.reply("/setRole id role")
    else:
        id = message.text.split(' ')[1]
        role = message.text.split(' ')[2]
        user = session.query(Person).filter_by(chatId=id).first()
        if user is None:
            await message.reply("Пользователь не найден")
        else:
            user.role = role
            session.commit()
            await message.reply("Роль изменнена")
        

async def main():
    print("BOT STARTED!")
    dp.bind_filter(isAdmin)
    dp.bind_filter(UserFilter)
    asyncio.create_task(activity())
    await dp.start_polling(dp, allowed_updates=False)


async def activity():
    print('Запустил авто активность')
    while True:
        await asyncio.sleep(5)
        accounts = session.query(Account).all()
        for account in accounts:
            account.activity()


if __name__ == '__main__':
    asyncio.run(main())
