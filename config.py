import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN_LLM')
api_key = os.getenv("YOUR_OPENAI_API_KEY")  # Устанавливаем ключ OpenAI

# Путь к базе данных
DB_PATH = "D:\\BD_prog\\education\\Geek_Brains_bot\\books_film_search_bot\\user_books_films.db"