# код в пичарм - тестовый бот для вывода случайного числа
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
import logging

import random

logging.basicConfig(level=logging.INFO)

API_TOKEN = 'Твой API телеграм'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет 😊")

# Хэндлер на команду /user
@dp.message(Command("пользователь"))
async def cmd_user(message: types.Message):
    await message.answer("Привет Пользователь 🤪")

# Хэндлер на команду /info
@dp.message(Command("info"))
async def cmd_info(message: types.Message):
    number = random.randint(1, 7)
    await message.answer("Я тестовый бот")
    await message.answer("Твоё число {number}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())