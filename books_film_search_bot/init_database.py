# инициализация, создане базы данных

import sqlite3

# Подключение к базе данных SQLite и создание таблиц
def init_database_func(db_path):
    conn = sqlite3.connect(db_path)
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