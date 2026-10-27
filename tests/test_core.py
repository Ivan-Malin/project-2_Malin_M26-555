from copy import deepcopy

from primitive_db.core import create_table, drop_table


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
    assert new_metadata == propper_new_metadata, (
        "create_table некорректно добавляет таблицу к уже существующей"
    )


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
