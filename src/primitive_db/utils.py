"""Содержит вспомогательные функции (такие как работа с файлами)."""

import json


def load_metadata(filepath: str) -> dict:
    """Загружает данные из JSON-файла.

    Возвращает пустой словарь если файла нет.

    Args:
        filepath (str): путь до файла

    Returns:
        dict: содержимое файла

    """
    try:
        with open(filepath) as f:
            content = f.read()
            return json.loads(content)
    except FileNotFoundError:
        # Отвратительный подход, лучше передавать ошибку
        # FileNotFoundError как есть. Но тз есть тз...
        return {}


def save_metadata(filepath: str, data: dict) -> None:
    """Сохраняет данные в JSON-файл.

    Args:
        filepath (str): путь до файла
        data (dict): содержимое файла

    """
    if not isinstance(data, dict):
        msg = "Некорректный тип входных данных"
        raise TypeError(msg)

    # Все ошибки, связанные с открытием файла,
    # пробрасываем дальше
    with open(filepath, "w") as f:
        f.write(
            json.dumps(data, ensure_ascii=False),
        )
