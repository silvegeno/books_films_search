# Функция для сохранения рекомендаций в базу данных
def save_recomendations_func(user_id, data, db_path):
    from datetime import datetime  # Для работы с датами
    import sqlite3  # Работа с локальной базой данных SQLite
    conn = sqlite3.connect(db_path)
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