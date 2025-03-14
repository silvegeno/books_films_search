import sqlite3
from datetime import datetime
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# Функция для получения предыдущих рекомендаций пользователя
def get_user_recommendations(db_path, user_id, limit=10):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT id, author, title, movie, date FROM recommendations
    WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?
    ''', (user_id, limit))

    results = cursor.fetchall()
    conn.close()

    return results


# Обработчик кнопки просмотра истории
async def show_history(bot, user_id, db_path, is_callback=False):
    # Получаем историю рекомендаций для пользователя
    recommendations = get_user_recommendations(db_path, user_id)

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


# Регистрация обработчиков
def register_history_handlers(dp, bot, db_path):
    from aiogram.filters import Command

    @dp.message(Command("history"))
    async def handle_history_command(message):
        await show_history(bot, message.from_user.id, db_path)

    @dp.callback_query(lambda c: c.data == "show_history")
    async def handle_history_button(callback):
        await show_history(bot, callback.from_user.id, db_path, is_callback=True)