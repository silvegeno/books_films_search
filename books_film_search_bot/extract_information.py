# Функция для извлечения информации из текста рекомендаций
def extract_information_func(text):
    import re
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