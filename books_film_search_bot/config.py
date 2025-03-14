import os
from dotenv import load_dotenv

load_dotenv()

token_telegram = os.getenv('BOT_TOKEN_LLM')
api_key = os.getenv("YOUR_OPENAI_API_KEY")  # Устанавливаем ключ OpenAI

# Путь к базе данных
db_path = os.getenv('DB_PATH')
admin_id = os.getenv('ADMIN_ID')
