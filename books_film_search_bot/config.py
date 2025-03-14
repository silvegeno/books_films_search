# Задание переменных
import os
from dotenv import load_dotenv

load_dotenv()

token_telegram = os.getenv('BOT_TOKEN_LLM') # API telegram
api_key = os.getenv("YOUR_OPENAI_API_KEY")  # Устанавливаем ключ OpenAI

db_path = os.getenv('DB_PATH')  # Путь к базе данных
admin_id = os.getenv('ADMIN_ID')    # id telegram администратора для отправки сообщений
