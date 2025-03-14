# Функция для сохранения рекомендаций в базу данных
import sqlite3  # Работа с локальной базой данных SQLite


def load_user_func(db_path, user_id_now):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * from users WHERE user_id = ?
    ''', (int(user_id_now),))

    rows = cursor.fetchall()

    # Начальные значения данных пользователя
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
    else:
        print("Пользователь не найден.")

    conn.close()

    return user_no, username, user_first_name, user_last_name
