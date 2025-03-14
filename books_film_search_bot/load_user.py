# Функция для сохранения рекомендаций в базу данных
import sqlite3  # Работа с локальной базой данных SQLite


def load_user_func(db_path, user_id_now):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Вставляем данные в таблицу
    # (795375565, 'anp_nik', 'ANP', None, None, 'Мужчина', '41-60 лет', None, 'ru', '2025-03-09 08:52:40')

    cursor.execute(f"PRAGMA table_info({"users"})")
    columns = [row[1] for row in cursor.fetchall()]  # Извлекаем имена столбцов
    print('columns', columns)

    cursor.execute('''
    SELECT * from users WHERE user_id = ?
    ''', (int(user_id_now),))

    rows = cursor.fetchall()

    username = 'Нет'
    user_first_name  = 'Нет'
    user_last_name = 'Нет'
    user_no = 'Нет'

    if rows:
        for row in rows:
            user_id, telegram_username, first_name, last_name, phone_number, gender, age, date_of_birth, email, language_code, registration_date = row  # Распаковываем кортеж
            username = telegram_username
            user_first_name = first_name
            user_last_name = last_name
            user_no = 'Пользователь: '
            #print(f"Username: {telegram_username}, Имя: {first_name}, Фамилия: {last_name}")
    else:
        print("Пользователь не найден.")

    conn.close()

    return user_no, username, user_first_name, user_last_name

# user_id_now = 795375565
# db_path = "D:\\BD_prog\\education\\Geek_Brains_bot\\books_film_search_bot\\user_books_films.db"
#
# user_no, username, user_first_name, user_last_name = load_user_func(DB_PATH, user_id_now)
# print(f"{user_no} username: {username}, ФИО: {user_first_name}, {user_last_name}")