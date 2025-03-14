# Телеграм бот для поиска книг и фильмов под настроение.#
# Для запуска используется файл "books_search9_2.py".
# # Бот задает 5 вопросов пользователю и подбирает с помощью ChatGPT книгу и фильм под текущее настроение пользователя.
# # После получения рекомендаций можно:
# просмотреть историю рекомендаций;
# еще раз попросить рекомендовать книгу и фильм;
# заново ответить на вопросы и получить рекомендации по книге и фильму.

import asyncio, os  # Асинхронная работа бота и система
import logging  # Логирование работы бота
from openai import OpenAI  # Добавляем библиотеку OpenAI
import sqlite3  # Локальная база данных SQLite, регулярные выражения
from datetime import datetime  # Для работы с датами
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

from config import token_telegram, api_key, db_path, admin_id
from questions_all import questions # вопросы пользователю о настроении
from init_database import init_database_func    # создание базы данных
from load_user import load_user_func    # Загрузим данные пользователя для отправки админу
from history_handler import register_history_handlers  # Импорт обработчиков истории
from save_recomendations import save_recomendations_func
from extract_information import extract_information_func


# Инициализация базы данных
init_database_func(db_path)

bot = Bot(token=token_telegram)
dp = Dispatcher()

user_answers = {}  # Словарь для хранения ответов пользователя
user_profiles = {}  # Словарь для хранения информации о поле и возрасте пользователей
user_search_history = {} # Словарь для хранения истории поиска пользователей
exclude_books_titles = ''     # Список найденных книг для исключения
exclude_films_titles = ''    # Список найденных фильмов для исключения


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
                           f"Привет, {user_name}! Я помогу подобрать книгу и фильм под Ваше настроение. Нажмите Старт.",
                           reply_markup=keyboard)


# Обработчик нажатия кнопки Старт
@dp.callback_query(lambda c: c.data == "button_start")
async def handle_start_button(callback: types.CallbackQuery):
    user = callback.from_user
    user_id = user.id

    conn = sqlite3.connect(db_path) # Подключение к базе данных
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
        [InlineKeyboardButton(text="От 10 до 18 лет", callback_data="age_18"),
         InlineKeyboardButton(text="19-25 лет", callback_data="age_19_25")],
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
    age_groups = {"age_18": "От 10 до 18 лет", "age_19_25": "19-25 лет", "age_26_40": "26-40 лет", "age_41_60": "41-60 лет",
                  "age_60": "Старше 60 лет"}
    user_profiles[user_id]["age"] = age_groups[callback.data]

    # Подключение к базе данных
    conn = sqlite3.connect(db_path)
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
        await analyze_results(user_id, exclude_books_titles, exclude_films_titles)


# Обработчик ответов пользователя на вопросы теста.
# Обработчик вызывается только для callback_data в формате число_число
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
async def analyze_results(user_id, exclude_books_titles, exclude_films_titles):
    if user_id in user_answers:
        await bot.send_message(user_id, f"Минутку, обращаюсь к ИИ за советом...")

        user_data = user_profiles.get(user_id, {})
        user_profile = f"Пол: {user_data.get('gender', 'Не указан')}, Возраст: {user_data.get('age', 'Не указан')}"
        user_profile += "".join(user_answers[user_id])

        client = OpenAI(api_key=api_key)

        # ------------ Подбор книги  ------------
        exclude_items_books = 'Спасибо'
        exclude_items_films = 'Спасибо'

        # Исключим ранее найденные книги
        if exclude_books_titles != '':
            exclude_items_books = 'Исключи из поиска: ' + exclude_books_titles

        chatgpt_prompt = f"""
        Подбери книгу для читателя со следующим психологическим портретом:
        {user_profile}. {exclude_items_books}
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
        # Исключаем ранее найденные фильмы
        if exclude_films_titles != '':
            exclude_items_films = 'Исключи из поиска: ' + exclude_films_titles

        chatgpt_prompt = f"""
            Подбери фильм для читателя со следующим психологическим портретом:
            {user_profile}. {exclude_items_films}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system",
                       "content": "Ты эксперт по фильмам, который подбирает фильмы по данным о человеке и под его настроение. В конце ответа напиши ==Фильм: <название фильма> =="},
                      {"role": "user", "content": chatgpt_prompt}],
            temperature=0.7
        )
        movie_recommendation = response.choices[0].message.content.strip()

        await bot.send_message(user_id, f"🎬 Я подобрал Вам фильм: \n{movie_recommendation}")

        # Объединяем рекомендации книги и фильма для сохранения в базу
        full_text = f"{book_recommendation}\n{movie_recommendation}"

        # Извлекаем данные из текста
        extracted_info = extract_information_func(full_text)

        # Сохраняем рекомендации в базу данных
        save_recomendations_func(user_id, extracted_info, db_path)

        # Сохраняем результаты поиска в истории пользователя
        if user_id not in user_search_history:
            user_search_history[user_id] = []

        # Добавляем текущий результат в историю
        user_search_history[user_id].append(extracted_info)

        # Отправляем данные пользователя администратору
        current_date = datetime.now().strftime("%Y-%m-%d")
        user_no, username, user_first_name, user_last_name = load_user_func(db_path, user_id)
        await bot.send_message(admin_id, f"{current_date}, {user_no} {username}, ФИО: {user_first_name}, {user_last_name}. Найдено: {extracted_info}")

        # Добавляем кнопки для повторного поиска и нового опроса
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 История поиска книг и фильмов", callback_data="show_history")],
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

    # Получаем историю поиска пользователя для исключения уже найденных книги и фильма
    # Список полученных книг по названию
    exclude_books_titles_list = [item['title'] for item in user_search_history[user_id]]
    exclude_books_titles = ', '.join(exclude_books_titles_list)

    # Список полученных фильмов по названию
    exclude_films_titles_list = [item['movie'] for item in user_search_history[user_id]]
    exclude_films_titles = ', '.join(exclude_films_titles_list)

    await bot.send_message(user_id, "Ищу новые книгу и фильм...")

    # Вызываем функцию поиска с исключениями
    await analyze_results(user_id, exclude_books_titles, exclude_films_titles)


# Обработчик кнопки "Поменялось настроение? Ответь на вопросы еще раз!"
@dp.callback_query(lambda c: c.data == "new_questionnaire")
async def handle_new_questionnaire(callback: types.CallbackQuery):
    print('callback:', callback)
    user_id = callback.from_user.id
    await callback.message.delete()

    # Очищаем предыдущие ответы пользователя и начинаем новый опрос
    user_answers[user_id] = []
    await bot.send_message(user_id, "Давай уточним твое текущее настроение!")
    await ask_question(user_id, 0)


# Функция запуска бота. Настраивает логирование и начинает поллинг.
async def main():
    logging.basicConfig(level=logging.INFO)

    # Регистрация обработчиков истории
    register_history_handlers(dp, bot, db_path)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())