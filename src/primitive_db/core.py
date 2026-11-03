"""Содержит основную логику работы с таблицами и данными высокоуровнеого."""

# Замечание по реализации core.py
# - исходя из ТЗ (исходной структуры), саму реализацию
#   без нарушения ТЗ адекватно было не написать (но
#   если делать неадекватно, то вопросов нет)
# - например у нас есть функции insert и прочие, в которых
#   в ТЗ просили возвращать сами данные. Так и не было
#   понятно по ТЗ требуется ли там имутабильность аргументов
#   или нет. Исходя из формулировки она там желательна,
#   но из-за этого везде появляются операции копирования,
#   что стоят непомерно дорого...
# - исполнителем было принято решение строго следовать ТЗ
#   и сделать (т.к. это логически для данных формулировок
#   более корректно) аргументы функции неизменяемыми

# Копирование можно было расписать вручную, но deepcopy
# сделает это корректнее и быстрее
from copy import deepcopy
from typing import Any

from primitive_db.constants import DATA_PATH
from primitive_db.errors import TableAlreadyExistsError, TableIsMissingError
from primitive_db.tables import Table, is_columns_propper
from primitive_db.utils import (
    CopyPolicy,
    get_table_path,
    is_table_structure_free,
)


def create_table(
    metadata: dict,
    table_name: str,
    columns: list[tuple[str, type]],
    data_path: str = DATA_PATH,
) -> dict:
    """Создаёт таблицу в хранилище с метаданными metadata.

    Args:
        metadata (dict): метаданные хранилища таблиц
        table_name (str): название таблицы
        columns (List[Tuple[str, str]]): упорядоченный список столбцов
            формата ("название", "тип_столбца"). тип_столбца один из
            COLUMN_TYPES
        data_path (str, optional): путь до папки с данными БД.
            По умолчанию берёт папку data проекта primitive_db.

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

    # Проверяем наличие ID
    columns_have_id = any(c[0] == "ID" for c in columns)
    if not columns_have_id:
        _columns = [("ID", "int")]
        _columns.extend(deepcopy(columns))
    else:
        _columns = deepcopy(columns)

    if not is_table_structure_free(metadata, table_name, data_path):
        msg = f"Таблица '{table_name}' уже существует."
        raise TableAlreadyExistsError(msg)

    table_path = get_table_path(table_name, data_path)

    _metadata["tables"][table_name] = {"columns": _columns, "path": table_path}
    Table.save_table_by_metadata(_metadata, Table(table_name, _columns), data_path)

    return _metadata


def drop_table(metadata: dict, table_name: str, data_path: str = DATA_PATH) -> dict:
    """Удаляет таблицу из хранилища с метаданными metadata.

    Args:
        metadata (dict): метаданные хранилища таблиц
        table_name (str): название таблицы
        data_path (str, optional): путь до папки с данными БД.
            По умолчанию берёт папку data проекта primitive_db.

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
        raise TableIsMissingError(msg)

    if table_name not in _metadata["tables"]:
        msg = f"metadata не содержит таблицы {table_name} для удаления"
        raise TableIsMissingError(msg)

    del _metadata["tables"][table_name]

    return _metadata


def insert(table_data: Table, values: list) -> Table:
    """Вставляет записи values в table_data.

    Args:
        table_data (Table): исходная таблица
        values (list): новая запись. Упорядоченная m-ка объектов,
            где m - количество колонок в таблице, за исключением
            колонки ID

    Returns:
        Table: изменённая таблица

    """
    _table_data = Table.copy(table_data)
    _table_data.insert(values)
    return _table_data


def select(table_data: Table, where_clause: dict[str, Any] | None = None) -> list[dict]:
    """Выбирает записи из таблицы, что соответствуют условию.

    Args:
        table_data (Table): исходная таблица.
        where_clause (dict[str, Any], optional): условие формата
            {column: value}. Если равен None, то возвращает все
            строки таблицы. По умолчанию None

    Returns:
        list[dict]: Записи таблицы

    """
    return table_data.select(where_clause, do_copy=CopyPolicy.DO_COPY)


def update(
    table_data: Table,
    set_clause: dict[str, Any],
    where_clause: dict[str, Any],
) -> tuple[Table, int]:
    """Обновляет записи в таблице table_data.

    Args:
        table_data (Table): исходная таблица
        set_clause (dict[str, Any]): Словарь {column: new_value} для обновления
        where_clause (dict[str, Any]): Словарь условий для поиска записей

    Returns:
        Table: изменённая таблица
        int: количество затронутых записей

    """
    _table_data = Table.copy(table_data)
    updated_count = _table_data.update(set_clause, where_clause)
    return _table_data, updated_count


def delete(table_data: Table, where_clause: dict[str, Any]) -> tuple[Table, int]:
    """Удаляет записи, удовлетворяющие условию.

    Args:
        table_data (Table): исходная таблица
        where_clause (dict[str, Any]):  условие формата {column: value}.
            для удаления записей

    Returns:
        Table: Обновлённая таблица
        int: количество затронутых записей

    """
    _table_data = Table.copy(table_data)
    deleted_count = _table_data.delete(where_clause)
    return _table_data, deleted_count
