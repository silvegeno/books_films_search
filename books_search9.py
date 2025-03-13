# Бот для подбора книг и фильмов в зависимости от текущего
# настроения человека.
# Он задает вопросы и на основе их формирует промпт.
# Его отправляет по API в chatGPT и получает ответ. Выводит его
# Данные сохраняет в базе sqlite
# git add .
# git commit -m 'Version with database users books films'
# git push origin main
import asyncio, os  # Асинхронная работа бота
import logging  # Логирование работы бота
from openai import OpenAI  # Добавляем библиотеку OpenAI
import sqlite3  # Работа с локальной базой данных SQLite
import re  # Для извлечения информации через регулярные выражения
from datetime import datetime  # Для работы с датами
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from config import TOKEN, api_key, DB_PATH
from questions_all import questions

# Подключение к базе данных SQLite и создание таблиц
def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Расширенная таблица для хранения информации о пользователях
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        telegram_username TEXT,
        first_name TEXT,
        last_name TEXT,
        phone_number TEXT,
        gender TEXT,
        age TEXT,
        email TEXT,
        language_code TEXT,
        registration_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Таблица для хранения рекомендаций
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        author TEXT,
        title TEXT,
        movie TEXT,
        date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')

    conn.commit()
    conn.close()


# Инициализация базы данных
init_database()

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_answers = {}  # Словарь для хранения ответов пользователя
user_profiles = {}  # Словарь для хранения информации о поле и возрасте пользователей

# Функция для извлечения информации из текста рекомендаций
def extract_information(text):
    # Создаем шаблоны для извлечения информации
    author_pattern = r"==Автор: ([^=]+)=="
    title_pattern = r"==Название: ([^=]+)=="
    movie_pattern = r"==Фильм: ([^=]+)=="

    # Извлекаем информацию с помощью регулярных выражений
    author = re.search(author_pattern, text)
    title = re.search(title_pattern, text)
    movie = re.search(movie_pattern, text)

    # Подготавливаем результаты
    result = {
        'author': author.group(1).strip() if author else None,
        'title': title.group(1).strip() if title else None,
        'movie': movie.group(1).strip() if movie else None
    }

    return result


# Функция для сохранения рекомендаций в базу данных
def save_recommendation(user_id, data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Получаем текущую дату
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Вставляем данные в таблицу
    cursor.execute('''
    INSERT INTO recommendations (user_id, author, title, movie, date)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, data.get('author'), data.get('title'), data.get('movie'), current_date))

    conn.commit()
    conn.close()

    return cursor.lastrowid


# Функция для получения предыдущих рекомендаций пользователя
def get_user_recommendations(user_id, limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT id, author, title, movie, date FROM recommendations
    WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?
    ''', (user_id, limit))

    results = cursor.fetchall()
    conn.close()

    return results


@dp.message(Command("start"))
async def ask_user_info(message: types.Message):
    print('---1 Старт---')
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Приветственное сообщение с кнопкой Старт
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Старт", callback_data="button_start")]
    ])
    await bot.send_message(user_id,
                           f"Привет, {user_name}! Я бот, который поможет подобрать книгу и фильм под Ваше настроение. Нажмите Старт, чтобы начать.",
                           reply_markup=keyboard)

# Обработчик нажатия кнопки Старт
@dp.callback_query(lambda c: c.data == "button_start")
async def handle_start_button(callback: types.CallbackQuery):
    user = callback.from_user
    user_id = user.id

    # Подключение к базе данных
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Проверяем наличие пользователя в базе данных
    cursor.execute("SELECT gender, age FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    # Если пользователь новый, сохраняем базовую информацию
    if not user_data:
        cursor.execute("""
        INSERT INTO users (
            user_id, 
            telegram_username, 
            first_name, 
            last_name,
            language_code
        ) VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            user.username,
            user.first_name,
            user.last_name,
            user.language_code
        ))
        conn.commit()

    conn.close()

    # Инициализируем массив ответов пользователя
    user_answers[user_id] = []

    # Удаляем сообщение с кнопкой Старт
    await callback.message.delete()

    if user_data:
        # Если пользователь уже есть в базе, загружаем его данные
        gender, age = user_data
        user_profiles[user_id] = {"gender": gender, "age": age}
        await bot.send_message(user_id, f"Отлично {user.username}, теперь ответьте на несколько вопросов о своем настроении!")
        await ask_question(user_id, 0)
    else:
        # Если пользователь новый, запрашиваем информацию
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Мужчина", callback_data="gender_male"),
             InlineKeyboardButton(text="Женщина", callback_data="gender_female")]
        ])
        await bot.send_message(user_id, "Укажите пожалуйста свой пол:", reply_markup=keyboard)


# Обработчик выбора пола пользователя. После выбора запрашивает возраст.
@dp.callback_query(lambda c: c.data.startswith("gender_"))
async def handle_gender(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    gender = "Мужчина" if callback.data == "gender_male" else "Женщина"
    user_profiles[user_id] = {"gender": gender, "age": None}
    await callback.message.delete()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="До 15 лет", callback_data="age_15"),
         InlineKeyboardButton(text="16-25 лет", callback_data="age_16_25")],
        [InlineKeyboardButton(text="26-40 лет", callback_data="age_26_40"),
         InlineKeyboardButton(text="41-60 лет", callback_data="age_41_60")],
        [InlineKeyboardButton(text="Старше 60 лет", callback_data="age_60")]]
    )
    await bot.send_message(user_id, "Сколько Вам лет?", reply_markup=keyboard)


# Обработчик выбора возраста пользователя. После выбора начинает тест.
@dp.callback_query(lambda c: c.data.startswith("age_"))
async def handle_age(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    age_groups = {"age_15": "До 15 лет", "age_16_25": "16-25 лет", "age_26_40": "26-40 лет", "age_41_60": "41-60 лет",
                  "age_60": "Старше 60 лет"}
    user_profiles[user_id]["age"] = age_groups[callback.data]

    # Подключение к базе данных
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Сохранение данных в SQLite
    cursor.execute(
        "INSERT INTO users (user_id, gender, age) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET gender = excluded.gender, age = excluded.age",
        (user_id, user_profiles[user_id]["gender"], user_profiles[user_id]["age"]))
    conn.commit()
    conn.close()

    await callback.message.delete()
    # Выводим новое сообщение после сбора данных о поле и возрасте
    await bot.send_message(user_id, f"Отлично {user_name}, теперь ответьте на несколько вопросов о своем настроении!")
    await ask_question(user_id, 0)


# Функция отправляет пользователю вопросы теста, предлагая варианты ответов.
async def ask_question(user_id, question_index):
    if question_index < len(questions):
        question, options = questions[question_index]
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=option, callback_data=f"{question_index}_{i}")]
                for i, option in enumerate(options)
            ]
        )
        await bot.send_message(user_id, question, reply_markup=keyboard)
    else:
        await analyze_results(user_id)


# Обработчик ответов пользователя на вопросы теста.
# Изменена фильтрация: теперь этот обработчик вызывается только для callback_data в формате число_число
@dp.callback_query(lambda c: c.data and "_" in c.data and c.data.split("_")[0].isdigit())
async def handle_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    question_index, answer_index = map(int, callback.data.split("_"))
    # Записываем текст ответа
    user_answers.setdefault(user_id, []).append(
        f"{question_index + 1}: '{['Сейчас настроение: ', 'Посмотрю фильм: ', 'Привлекает в книгах: ', 'Мне хочется: ', 'Новое или классика: '][question_index]}{questions[question_index][1][answer_index]}'")
    await callback.message.delete()
    await ask_question(user_id, question_index + 1)


# Анализирует ответы пользователя и отправляет запрос в ChatGPT
# для подбора книги в соответствии с его психологическим профиле
async def analyze_results(user_id):
    if user_id in user_answers:
        await bot.send_message(user_id, f"Минутку, обращаюсь к ИИ за советом...")

        user_data = user_profiles.get(user_id, {})
        user_profile = f"Пол: {user_data.get('gender', 'Не указан')}, Возраст: {user_data.get('age', 'Не указан')}"
        user_profile += "".join(user_answers[user_id])

        client = OpenAI(api_key=api_key)

        # Подбор книги
        chatgpt_prompt = f"""
        Подбери книгу для читателя со следующим психологическим портретом:
        {user_profile}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system",
                       "content": "Ты книжный эксперт, который подбирает книги по данным о человеке и под его настроение. В конце ответа напиши ==Автор: <имя автора> ==, ==Название: <название книги> =="},
                      {"role": "user", "content": chatgpt_prompt}]
        )
        book_recommendation = response.choices[0].message.content.strip()
        await bot.send_message(user_id, f"📖 Я подобрал Вам книгу: \n{book_recommendation}")

        # Подбор фильма
        chatgpt_prompt = f"""
            Подбери фильм для читателя со следующим психологическим портретом:
            {user_profile}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system",
                       "content": "Ты эксперт по фильмам, который подбирает фильмы по данным о человеке и под его настроение. В конце ответа напиши ==Фильм: <название фильма> =="},
                      {"role": "user", "content": chatgpt_prompt}],
            temperature=0.7
        )
        movie_recommendation = response.choices[0].message.content.strip()
        # print('recommendation:/n', movie_recommendation)
        await bot.send_message(user_id, f"🎬 Я подобрал Вам фильм: \n{movie_recommendation}")

        # Объединяем рекомендации книги и фильма для сохранения в базу
        full_text = f"{book_recommendation}\n{movie_recommendation}"

        # Извлекаем данные из текста
        extracted_info = extract_information(full_text)

        # Сохраняем рекомендации в базу данных
        save_recommendation(user_id, extracted_info)

        # Добавляем кнопки для повторного поиска и нового опроса
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 История Ваших рекомендаций", callback_data="show_history")],
            [InlineKeyboardButton(text="🔄 Я запомнил Ваше настроение. Поищем еще раз?", callback_data="search_again")],
            [InlineKeyboardButton(text="😊 Поменялось настроение? Ответьте на вопросы еще раз!", callback_data="new_questionnaire")]
        ])
        await bot.send_message(user_id, "Я сохранил эти рекомендации. Что делаем дальше?",
                               reply_markup=keyboard)

        # Сохраняем ответы пользователя в переменную для возможного повторного использования
        # НЕ удаляем user_answers[user_id]


# Обработчик кнопки "Поищем еще раз?"
@dp.callback_query(lambda c: c.data == "search_again")
async def handle_search_again(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()

    # Используем сохраненные ответы для повторного поиска
    await bot.send_message(user_id, "Ищу новые рекомендации на основе Ваших предыдущих ответов...")
    await analyze_results(user_id)


# Обработчик кнопки "Поменялось настроение? Ответь на вопросы еще раз!"
@dp.callback_query(lambda c: c.data == "new_questionnaire")
async def handle_new_questionnaire(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.delete()

    # Очищаем предыдущие ответы пользователя и начинаем новый опрос
    user_answers[user_id] = []
    await bot.send_message(user_id, "Давай уточним твое текущее настроение!")
    await ask_question(user_id, 0)


# Обработчик кнопки просмотра истории
async def show_history(user_id, is_callback=False):
    # Получаем историю рекомендаций для пользователя
    recommendations = get_user_recommendations(user_id)

    if not recommendations:
        await bot.send_message(user_id, "У Вас пока нет истории рекомендаций.")
        return

    response = "📚 Ваша история рекомендаций:\n\n"
    for rec in recommendations:
        rec_id, author, title, movie, date = rec
        response += f"📅 Дата: {date}\n"
        if author and title:
            response += f"📖 Книга: {title} (автор: {author})\n"
        elif title:
            response += f"📖 Книга: {title}\n"
        if movie:
            response += f"🎬 Фильм: {movie}\n"
        response += "---\n"

    if is_callback:
        # Специфичное поведение для callback
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Старт", callback_data="button_start")]
        ])
        await bot.send_message(user_id, response)
        await bot.send_message(user_id, "Для еще одного поиска нажмите Старт.", reply_markup=keyboard)
    else:
        await bot.send_message(user_id, response)

# Обновленные обработчики
@dp.message(Command("history"))
async def handle_history_command(message: types.Message):
    await show_history(message.from_user.id)

@dp.callback_query(lambda c: c.data == "show_history")
async def handle_history_button(callback: types.CallbackQuery):
    await show_history(callback.from_user.id, is_callback=True)


# Функция запуска бота. Настраивает логирование и начинает поллинг.
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())