from copy import deepcopy

import pytest

from primitive_db.core import create_table, delete, drop_table, insert, select, update
from primitive_db.errors import TableAlreadyExistsError
from primitive_db.tables import Table


# Вспомогательная функция
def _create_test_table(name="users", columns=None, data=None):
    """Создает тестовую таблицу для использования в тестах core."""
    if columns is None:
        columns = [
            ("ID", "int"),
            ("name", "str"),
            ("age", "int"),
            ("is_active", "bool"),
        ]
    return Table(name=name, columns=columns, data=data)


# Основное тестирование


def test_create_table():
    # Проверяем создание одной таблицы
    metadata = {}
    table_name = "лекарства"
    columns = [
        ("название", "str"),
        ("описание", "str"),
        ("мин_возраст", "int"),
        ("можно_принимать_беременным", "bool"),
    ]

    propper_metadata = deepcopy(metadata)
    propper_table_name = deepcopy(table_name)
    propper_columns = deepcopy(columns)
    c = [("ID", "int")]
    c.extend(columns)
    propper_new_metadata = {
        "tables": {
            table_name: {
                "columns": c,
            },
        },
    }

    new_metadata = create_table(metadata, table_name, columns)
    del new_metadata["tables"]["лекарства"]["path"]

    # Проверяем корректность входных аргументов
    assert id(metadata) != id(new_metadata) and metadata == propper_metadata, (
        "create_table меняет исходный словарь!"
    )
    assert table_name == propper_table_name, "create_table меняет аргумент table_name!"
    assert columns == propper_columns, "create_table меняет аргумент columns!"
    # Проверяем
    assert new_metadata == propper_new_metadata, "create_table работает некорректно"

    # Проверяем добавление ещё одной таблицы
    metadata = new_metadata
    table_name = "аптеки"
    columns = [
        ("название", "str"),
        ("владелец", "str"),
        ("количество_сотрудников", "int"),
        ("работает", "bool"),
        ("ID", "int"),
    ]
    c = columns
    propper_new_metadata["tables"] |= {
        table_name: {
            "columns": c,
        },
    }

    new_metadata = create_table(metadata, table_name, columns)

    # Проверяем
    del new_metadata["tables"]["аптеки"]["path"]
    assert new_metadata == propper_new_metadata, (
        "create_table некорректно добавляет таблицу к уже существующей"
    )

    # Проверяем добавление дубля
    got_value_error_fl = False
    try:
        create_table(new_metadata, table_name, columns)
    except TableAlreadyExistsError:
        got_value_error_fl = True
    assert got_value_error_fl, "create_table не умеет отбрасывать создание дублей"


def test_create_table_wrong_inputs():
    got_type_error_fl = False
    try:
        create_table({}, 12345, [("название", "str")])
    except TypeError:
        got_type_error_fl = True
    assert got_type_error_fl, (
        "create_table не умеет обрабатывать неправилный table_name"
    )

    got_type_error_fl = False
    try:
        create_table({}, "аптеки", [("название", float)])
    except TypeError:
        got_type_error_fl = True
    assert got_type_error_fl, "create_table не умеет обрабатывать неправилный columns"

    got_type_error_fl = False
    try:
        create_table({}, "аптеки", [(float,)])
    except TypeError:
        got_type_error_fl = True
    assert got_type_error_fl, "create_table не умеет обрабатывать неправилный columns"

    got_type_error_fl = False
    try:
        create_table({}, "аптеки", [("название",)])
    except TypeError:
        got_type_error_fl = True
    assert got_type_error_fl, "create_table не умеет обрабатывать неправилный columns"

    got_type_error_fl = False
    try:
        create_table({}, "аптеки", "название")
    except TypeError:
        got_type_error_fl = True
    assert got_type_error_fl, "create_table не умеет обрабатывать неправилный columns"


def test_drop_table():
    metadata = {
        "tables": {
            "лекарства": {
                "columns": [
                    ("ID", "int"),
                    ("название", "str"),
                    ("описание", "str"),
                    ("мин_возраст", "int"),
                    ("можно_принимать_беременным", "bool"),
                ]
            },
            "аптеки": {
                "columns": [
                    ("ID", "int"),
                    ("название", "str"),
                    ("владелец", "str"),
                    ("количество_сотрудников", "int"),
                    ("работает", "bool"),
                ]
            },
        }
    }
    table_name = "аптеки"

    propper_new_metadata = {
        "tables": {
            "лекарства": {
                "columns": [
                    ("ID", "int"),
                    ("название", "str"),
                    ("описание", "str"),
                    ("мин_возраст", "int"),
                    ("можно_принимать_беременным", "bool"),
                ]
            }
        }
    }
    propper_metadata = deepcopy(metadata)
    propper_table_name = deepcopy(table_name)

    new_metadata = drop_table(metadata, table_name)

    assert id(metadata) != id(new_metadata) and metadata == propper_metadata, (
        "drop_table меняет исходный словарь!"
    )
    assert table_name == propper_table_name, "drop_table меняет аргумент table_name!"
    assert new_metadata == propper_new_metadata, "drop_table работает некорректно"


def test_drop_table_wrong_input():
    got_key_error_fl = False
    try:
        drop_table({}, "аптеки")
    except KeyError:
        got_key_error_fl = True
    assert got_key_error_fl, "drop_table не умеет обрабатывать неправилный table_name"


# Остальные тесты test_core.py сгенерировала нейронка под пристальным надзором,
# т.к. покрывать всё тестами вручную для ТЗ, в котором это даже
# не проверяют - просто overkill


def test_insert_basic():
    """Тест базовой вставки записи через core.insert"""
    table_data = _create_test_table(
        data=[{"ID": 1, "name": "Alice", "age": 25, "is_active": True}]
    )
    values = ["Bob", 30, False]

    propper_table_data = deepcopy(table_data)
    propper_values = deepcopy(values)

    new_table = insert(table_data, values)

    # Проверка неизменности исходных данных
    assert len(table_data.data) == 1, "insert изменил исходную таблицу!"
    assert table_data.data == propper_table_data.data, (
        "Данные в исходной таблице изменились!"
    )
    assert values == propper_values, "insert изменил входной список values!"

    # Проверка результата
    assert isinstance(new_table, Table), "insert должен возвращать объект Table!"
    assert len(new_table.data) == 2, "Новая таблица должна содержать 2 записи!"
    assert new_table.data[1]["name"] == "Bob", "Имя второй записи неверно!"
    assert new_table.data[1]["age"] == 30, "Возраст второй записи неверен!"
    assert new_table.data[1]["is_active"] is False, "Статус второй записи неверен!"
    assert new_table.data[1]["ID"] == 2, "ID должен быть сгенерирован автоматически!"


def test_insert_empty_table():
    """Тест вставки в пустую таблицу"""
    table_data = _create_test_table(data=[])
    values = ["Charlie", 40, True]

    new_table = insert(table_data, values)

    assert len(new_table.data) == 1
    assert new_table.data[0]["ID"] == 1
    assert new_table.data[0]["name"] == "Charlie"


def test_insert_wrong_values_count():
    """Тест вставки неверного количества значений"""
    table_data = _create_test_table()
    values = ["OnlyName"]  # Нужно 3 значения

    with pytest.raises(ValueError):
        insert(table_data, values)


def test_insert_wrong_types():
    """Тест вставки значений неверных типов"""
    table_data = _create_test_table()
    values = ["Name", "not_an_int", True]  # age должно быть int

    with pytest.raises(TypeError):
        insert(table_data, values)


def test_select_all():
    """Тест выборки всех записей"""
    initial_data = [
        {"ID": 1, "name": "Alice", "age": 25, "is_active": True},
        {"ID": 2, "name": "Bob", "age": 30, "is_active": False},
    ]
    table_data = _create_test_table(data=initial_data)

    result = select(table_data)

    assert isinstance(result, list), "select должен возвращать список!"
    assert len(result) == 2, "Должны быть выбраны все записи!"
    assert result[0]["name"] == "Alice"
    assert result[1]["name"] == "Bob"

    # Проверка что это копии (так как do_copy=DO_COPY по умолчанию в core.select)
    result[0]["name"] = "Modified"
    assert table_data.data[0]["name"] == "Alice", (
        "Изменение результата select повлияло на исходную таблицу!"
    )


def test_select_with_where():
    """Тест выборки с условием"""
    initial_data = [
        {"ID": 1, "name": "Alice", "age": 25, "is_active": True},
        {"ID": 2, "name": "Bob", "age": 30, "is_active": True},
        {"ID": 3, "name": "Charlie", "age": 35, "is_active": False},
    ]
    table_data = _create_test_table(data=initial_data)

    where_clause = {"is_active": True}
    result = select(table_data, where_clause)

    assert len(result) == 2, "Должны быть выбраны только активные пользователи!"
    assert all(r["is_active"] is True for r in result)
    assert any(r["name"] == "Alice" for r in result)
    assert any(r["name"] == "Bob" for r in result)


def test_select_no_matches():
    """Тест выборки без совпадений"""
    table_data = _create_test_table(
        data=[{"ID": 1, "name": "Alice", "age": 25, "is_active": True}]
    )

    result = select(table_data, {"name": "NonExistent"})

    assert len(result) == 0, "Результат должен быть пустым списком!"


def test_update_single_record():
    """Тест обновления одной записи"""
    initial_data = [
        {"ID": 1, "name": "Alice", "age": 25, "is_active": True},
        {"ID": 2, "name": "Bob", "age": 30, "is_active": False},
    ]
    table_data = _create_test_table(data=initial_data)

    set_clause = {"age": 31}
    where_clause = {"name": "Bob"}

    propper_table_data = deepcopy(table_data)

    new_table = update(table_data, set_clause, where_clause)

    # Проверка неизменности исходной таблицы
    assert table_data.data == propper_table_data.data, (
        "update изменил исходную таблицу!"
    )
    assert id(table_data) != id(new_table), "update должен возвращать новую таблицу!"

    # Проверка результата
    assert new_table.data[1]["age"] == 31, "Возраст Bob не обновился!"
    assert new_table.data[0]["age"] == 25, "Возраст Alice не должен был измениться!"


def test_update_multiple_records():
    """Тест обновления нескольких записей"""
    initial_data = [
        {"ID": 1, "name": "Alice", "age": 25, "is_active": False},
        {"ID": 2, "name": "Bob", "age": 30, "is_active": False},
    ]
    table_data = _create_test_table(data=initial_data)

    set_clause = {"is_active": True}
    where_clause = {"is_active": False}

    new_table = update(table_data, set_clause, where_clause)

    assert all(r["is_active"] is True for r in new_table.data), (
        "Все записи должны стать активными!"
    )


def test_update_nonexistent_column():
    """Тест обновления несуществующего столбца"""
    table_data = _create_test_table()

    with pytest.raises(KeyError):
        update(table_data, {"fake_col": "val"}, {"ID": 1})


def test_delete_single_record():
    """Тест удаления одной записи"""
    initial_data = [
        {"ID": 1, "name": "Alice", "age": 25, "is_active": True},
        {"ID": 2, "name": "Bob", "age": 30, "is_active": False},
    ]
    table_data = _create_test_table(data=initial_data)

    where_clause = {"name": "Alice"}
    propper_table_data = deepcopy(table_data)

    new_table = delete(table_data, where_clause)

    # Проверка неизменности исходной таблицы
    assert table_data.data == propper_table_data.data, (
        "delete изменил исходную таблицу!"
    )
    assert len(table_data.data) == 2, (
        "Количество записей в исходной таблице не должно измениться!"
    )

    # Проверка результата
    assert len(new_table.data) == 1, "В новой таблице должна остаться 1 запись!"
    assert new_table.data[0]["name"] == "Bob", "Должен остаться только Bob!"


def test_delete_multiple_records():
    """Тест удаления нескольких записей"""
    initial_data = [
        {"ID": 1, "name": "Alice", "age": 25, "is_active": False},
        {"ID": 2, "name": "Bob", "age": 30, "is_active": False},
        {"ID": 3, "name": "Charlie", "age": 35, "is_active": True},
    ]
    table_data = _create_test_table(data=initial_data)

    where_clause = {"is_active": False}

    new_table = delete(table_data, where_clause)

    assert len(new_table.data) == 1, "Должна остаться только 1 активная запись!"
    assert new_table.data[0]["name"] == "Charlie"


def test_delete_no_matches():
    """Тест удаления без совпадений"""
    initial_data = [{"ID": 1, "name": "Alice", "age": 25, "is_active": True}]
    table_data = _create_test_table(data=initial_data)

    new_table = delete(table_data, {"name": "Bob"})

    assert len(new_table.data) == 1, "Записи не должны быть удалены!"
    assert new_table.data[0]["name"] == "Alice"
