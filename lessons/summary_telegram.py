# Телеграм бот, который просматривает определенные каналы
# в телеграм и дает саммари, что там изменилось за день

# pip install aiogram telethon sumy python-dotenv
# Через Telethon: позволяет парсить посты с каналов (нужен API ID и API Hash от Telegram)
# Можно добавить автоматическую отправку отчета раз в день через apscheduler.
# Можно хранить историю сообщений, чтобы не дублировать старые посты.
# Можно прикрутить фильтрацию по ключевым словам.
# Хранение состояния (например, с SQLite или Redis, чтобы не повторять старые посты).

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from telethon import TelegramClient
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# 🔹 Токены и API-ключи
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен бота
API_ID = os.getenv("API_ID")        # Telegram API ID
API_HASH = os.getenv("API_HASH")    # Telegram API HASH

# 🔹 Список каналов, которые отслеживает бот
CHANNELS = ["@example_channel1", "@example_channel2"]

# 🔹 Настройка логирования
logging.basicConfig(level=logging.INFO)

# 🔹 Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot)

# 🔹 Инициализация Telethon-клиента
client = TelegramClient("session_name", API_ID, API_HASH)

async def fetch_messages():
    """Получает последние 5 сообщений из каналов и делает саммари."""
    summaries = []
    await client.start()  # Запускаем Telethon-клиент

    for channel in CHANNELS:
        async for message in client.iter_messages(channel, limit=5):  # Берём последние 5 постов
            if message.text:
                summary = summarize_text(message.text)
                summaries.append(f"🔹 **{channel}**: {summary}")

    await client.disconnect()  # Отключаем Telethon-клиент
    return "\n\n".join(summaries) if summaries else "Нет новых сообщений."

def summarize_text(text):
    """Создает краткое описание текста с помощью Sumy."""
    parser = PlaintextParser.from_string(text, Tokenizer("russian"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, 2)  # Берём 2 предложения
    return " ".join([str(sent) for sent in summary])

@dp.message_handler(commands=["start"])
async def start_command(message: Message):
    """Обработчик команды /start"""
    await message.answer("Привет! Я бот, который собирает сводки из каналов. Напиши /summary, чтобы получить отчёт.")

@dp.message_handler(commands=["summary"])
async def summary_command(message: Message):
    """Отправляет пользователю сводку изменений за день."""
    await message.answer("⏳ Генерирую сводку, подождите...")
    summary = await fetch_messages()
    await message.answer(summary)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.start())  # Убеждаемся, что Telethon подключен
    executor.start_polling(dp, skip_updates=True)
