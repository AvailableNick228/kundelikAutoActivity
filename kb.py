from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton



startMenu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3).add(
    KeyboardButton("💼 Аккаунты"),
)


accountsButtons = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("➕ Добавить"),
    KeyboardButton("➖ Удалить"),
).add(
    KeyboardButton("🔙 Назад"),
)

