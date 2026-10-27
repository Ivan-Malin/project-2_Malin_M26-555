"""Содержит основную логику работы с таблицами и данными."""

# Они необходимы для чистого кода...
from collections.abc import Sequence

# Копирование можно было расписать вручную, но deepcopy
# сделает это корректнее и быстрее
from copy import deepcopy


def is_columns_propper(columns: list[tuple[str, type]]) -> bool:
    """Проверяет является ли columns списком колонок таблицы.

    Args:
        columns (List[Tuple[str, type]]): _description_

    Returns:
        bool: является ли columns списком колонок таблицы.

    """
    # По хорошему это всё делать через классы, но т.з. есть т.з....
    if not isinstance(columns, Sequence):
        return False

    return all(
        isinstance(item, (list, tuple))
        and len(item) == len(("имя", type))
        and isinstance(item[0], str)
        and item[1] in (str, int, bool)
        for item in columns
    )


def create_table(
    metadata: dict, table_name: str, columns: list[tuple[str, type]],
) -> dict:
    """Создаёт таблицу в хранилище с метаданными metadata.

    Args:
        metadata (dict): метаданные хранилища таблиц
        table_name (str): название таблицы
        columns (List[Tuple[str, type]]): упорядоченный список столбцов
            формата ("название", тип_столбца). тип_столбца один из
            int, str, bool

    Raises:
        TypeError: В случае некорректных аргументов

    Returns:
        dict: метаданные хранилища таблиц с добавленной таблицей

    """
    if not isinstance(metadata, dict):
        msg = "metadata должен быть dict"
        raise TypeError(msg)
    if not isinstance(table_name, str):
        msg = "table_name должен быть str"
        raise TypeError(msg)
    if not is_columns_propper(columns):
        msg = "columns должен быть списком колонок"
        raise TypeError(msg)

    _metadata = deepcopy(metadata)
    if "tables" not in _metadata:
        _metadata["tables"] = {}

    _columns = [("ID", int)]
    _columns.extend(deepcopy(columns))
    _metadata["tables"][table_name] = {
        "columns": _columns,
    }

    return _metadata


def drop_table(metadata: dict, table_name: str) -> dict:
    """Удаляет таблицу из хранилища с метаданными metadata.

    Args:
        metadata (dict): метаданные хранилища таблиц
        table_name (str): название таблицы

    Returns:
        dict: метаданные хранилища таблиц без таблицы table_name

    """
    if not isinstance(metadata, dict):
        msg = "metadata должен быть dict"
        raise TypeError(msg)
    if not isinstance(table_name, str):
        msg = "table_name должен быть str"
        raise TypeError(msg)

    _metadata = deepcopy(metadata)

    if "tables" not in _metadata:
        msg = "metadata не содержит таблиц для удаления"
        raise KeyError(msg)

    if table_name not in _metadata["tables"]:
        msg = f"metadata не содержит таблицы {table_name} для удаления"
        raise KeyError(msg)

    del _metadata["tables"][table_name]

    return _metadata
