# Тестовый эхо бот
# t.me/LLM_chat_answer_bot
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

API_TOKEN = '7922282991:AAHB9P_F_eCofM1LIMgpa3euiSvlJBbpNEo'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет!\nЯ EchoBot!")

@dp.message()
async def echo(message: types.Message):
    await message.answer(message.text)

async def main():
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())

