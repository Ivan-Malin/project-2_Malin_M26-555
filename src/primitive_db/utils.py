"""Содержит вспомогательные функции (такие как работа с файлами)."""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any

from primitive_db.constants import DATA_PATH, DEFAULT_METADATA_CONTENT


class CopyPolicy(Enum):
    """Политика копирования элементов таблицы."""

    DO_NOT_COPY = 1
    DO_COPY = 2


class OverwritePolicy(Enum):
    """Политика перезаписи элементов таблицы."""

    DO_NOT_OVERWRITE = 1
    DO_OVERWRITE = 2


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

    Returns:
        bool: результат проверки

    """
    if not isinstance(data, dict):
        msg = "Некорректный тип входных данных"
        raise TypeError(msg)

    # Все ошибки, связанные с json, пробрасываем дальше.
    # json парсится до открытия файла из-за того, что "w"
    # режим перезатирает файл сразу после открытия
    result = json.dumps(data, ensure_ascii=False)
    # Все ошибки, связанные с открытием файла, пробрасываем дальше
    with open(filepath, "w") as f:
        f.write(result)


# load_table_data(table_name) и save_table_data(table_name, data)
# заменены их аналогами внутри класса Table в tables.py
# так намного более практично


def is_table_data_exist(table_name: str, data_path: str = DATA_PATH) -> bool:
    """Проверяет, существуют ли данные таблицы в БД.

    Args:
        table_name (str): название таблицы
        data_path (str): путь до папки с данными БД.
            По умолчанию берёт папку data проекта primitive_db.

    Returns:
        bool: результат проверки

    """
    return Path(get_table_path(table_name, data_path)).is_file()


def is_table_exist(metadata: dict, table_name: str, data_path: str = DATA_PATH) -> bool:
    """Проверяет, существует ли таблица в БД.

    Args:
        metadata (dict): метаданные БД
        table_name (str): название таблицы
        data_path (str, optional): путь до папки с данными БД.
            По умолчанию берёт папку data проекта primitive_db.

    Returns:
        bool: результат проверки

    """
    if "tables" not in metadata:
        return False

    return table_name in metadata["tables"]


def is_table_structure_free(
    metadata: dict,
    table_name: str,
    data_path: str = DATA_PATH,
) -> bool:
    """Проверяет, есть ли в структуре остатки от прудыдущей таблицы.

    Args:
        metadata (dict): метаданные БД
        table_name (str): название таблицы
        data_path (str, optional): путь до папки с данными БД.
            По умолчанию берёт папку data проекта primitive_db.

    Returns:
        bool: результат проверки

    """
    return not is_table_exist(
        metadata,
        table_name,
        data_path,
    ) and not is_table_data_exist(
        table_name,
        data_path,
    )


def get_table_path(table_name: str, data_path: str = DATA_PATH) -> str:
    """Получает путь до таблицы table_name в структуре БД.

    Args:
        table_name (str): _description_
        data_path (str, optional): путь до папки с данными БД.
            По умолчанию берёт папку data проекта primitive_db.

    Returns:
        str: путь до таблицы

    """
    return str(Path(data_path) / Path(table_name + ".json"))


def create_database_structure_if_none(metadata_path: str) -> None:
    """Создаёт структуру таблиц, если та отсутствует в директории.

    Args:
        metadata_path (str): путь до metadata

    """
    metadata = load_metadata(metadata_path)
    if metadata == {}:
        prepare_full_path(metadata_path)
        save_metadata(metadata_path, DEFAULT_METADATA_CONTENT)


def validate_value(value: Any, expected_type_str: str) -> Any:
    """Проверяет и приводит значение к ожидаемому типу.

    Args:
        value (Any): Значение для проверки.
        expected_type_str (str): Один из типов "int", "str", "bool".

    Returns:
        Приведенное значение.

    Raises:
        TypeError: Если значение не соответствует типу.
        NotImplementedError: Если обработчик для типа не написан.

    """
    if expected_type_str == "int":
        if isinstance(
            value,
            bool,
        ):  # bool является подклассом int в Python, нужно исключить
            msg = f"Ожидался int, получен bool: {value}"
            raise TypeError(msg)
        if not isinstance(value, int):
            # Попытка конвертации строки в int, если это возможно
            msg = f"Ожидался int, получен {type(value)}: {value}"
            raise TypeError(
                msg,
            )
        return value
    if expected_type_str == "str":
        if not isinstance(value, str):
            msg = f"Ожидался str, получен {type(value)}: {value}"
            raise TypeError(
                msg,
            )
        return value
    if expected_type_str == "bool":
        if not isinstance(value, bool):
            msg = f"Ожидался bool, получен {type(value)}: {value}"
            raise TypeError(
                msg,
            )
        return value
    msg = f"Неизвестный тип: {expected_type_str}"
    raise NotImplementedError(msg)


def prepare_full_path(filepath: str) -> None:
    """Создаёт полный путь до файла, включая подпапки, но не включая сам файл.

    Args:
        filepath (str): полный путь до файла

    """
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_current_path() -> str:
    """Возвращает текущий рабочий путь.

    Returns:
        str: путь

    """
    return os.path.dirname(__file__)


def remove_file(filepath: str) -> None:
    """Удаляет файл."""
    os.remove(filepath)
