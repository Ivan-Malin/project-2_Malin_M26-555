from copy import deepcopy
from pathlib import Path

import pytest

from primitive_db.core import create_table
from primitive_db.tables import Table, does_columns_have_id, is_columns_propper
from primitive_db.utils import CopyPolicy

# Замечание проверяющему - часть тестовых файлов были отданы на откуп Qwen'у,
# т.к. тесты от нейросети (под пристальным ревью) лучше, чем никаких тестов вообще.
# Да и в ТЗ не оговорено, что вообще тесты нужны

# ==================== Тесты вспомогательных функций ====================


def test_is_columns_propper_valid():
    """Тест корректной проверки схемы."""
    valid_columns = [("ID", "int"), ("name", "str"), ("age", "int")]
    assert is_columns_propper(valid_columns) is True


def test_is_columns_propper_invalid_types():
    """Тест проверки схемы с неверными типами."""
    invalid_columns = [("ID", "int"), ("name", float)]
    assert is_columns_propper(invalid_columns) is False


def test_is_columns_propper_not_sequence():
    """Тест проверки не-списка."""
    assert is_columns_propper("not a list") is False
    assert is_columns_propper(123) is False


def test_does_columns_have_id_true():
    """Тест наличия ID в схеме."""
    columns = [("ID", "int"), ("name", "str")]
    assert does_columns_have_id(columns) is True


def test_does_columns_have_id_false():
    """Тест отсутствия ID в схеме."""
    columns = [("name", "str"), ("age", "int")]
    # Функция должна вернуть False, но внутри она вызывает TypeError если схема плохая.
    # Здесь схема плохая именно отсутствием ID? Нет, просто нет ID.
    # Но does_columns_have_id сначала проверяет is_columns_propper.
    # Эта схема валидна по структуре, просто нет ID.
    assert does_columns_have_id(columns) is False


def test_does_columns_have_id_wrong_type_for_id():
    """Тест, когда ID есть, но тип не int."""
    columns = [("ID", "str")]
    assert does_columns_have_id(columns) is False


def test_does_columns_have_id_bad_columns_raises():
    """Тест, что передается некорректная схема."""
    with pytest.raises(TypeError):
        does_columns_have_id("bad")


# ==================== Тесты инициализации Table ====================


def test_table_init_basic():
    """Тест базовой инициализации таблицы."""
    name = "users"
    columns = [("ID", "int"), ("name", "str")]
    table = Table(name=name, columns=columns)

    assert table.name == name
    assert table.columns == columns
    assert table.data == []


def test_table_init_with_data():
    """Тест инициализации с данными."""
    data = [{"ID": 1, "name": "Alice"}]
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")], data=data)

    assert len(table.data) == 1
    assert table.data[0]["name"] == "Alice"


def test_table_init_copy_policy_do_copy():
    """Тест политики копирования DO_COPY."""
    original_data = [{"ID": 1, "name": "Alice"}]
    original_columns = [("ID", "int"), ("name", "str")]

    table = Table(
        name="users",
        columns=original_columns,
        data=original_data,
        do_copy=CopyPolicy.DO_COPY,
    )

    # Изменяем исходные данные
    original_data.append({"ID": 2, "name": "Bob"})
    original_columns.append(("age", "int"))

    # Данные в таблице не должны измениться
    assert len(table.data) == 1
    assert len(table.columns) == 2


def test_table_init_copy_policy_do_not_copy():
    """Тест политики копирования DO_NOT_COPY."""
    original_data = [{"ID": 1, "name": "Alice"}]

    table = Table(
        name="users",
        columns=[("ID", "int"), ("name", "str")],
        data=original_data,
        do_copy=CopyPolicy.DO_NOT_COPY,
    )

    # Изменяем исходные данные
    original_data.append({"ID": 2, "name": "Bob"})

    # Данные в таблице должны измениться (так как это ссылка)
    assert len(table.data) == 2


def test_table_init_missing_id_raises():
    """Тест ошибки при отсутствии ID в схеме."""
    with pytest.raises(ValueError, match="columns не содержит поля ID"):
        Table(name="test", columns=[("name", "str")])


def test_table_init_invalid_name_raises():
    """Тест ошибки при неверном имени."""
    with pytest.raises(ValueError):
        Table(name="", columns=[("ID", "int")])

    with pytest.raises(ValueError):
        Table(name=123, columns=[("ID", "int")])


def test_table_init_invalid_columns_raises():
    """Тест ошибки при неверной схеме."""
    with pytest.raises(TypeError):
        Table(name="test", columns="not a list")


def test_table_init_invalid_data_types_raises():
    """Тест ошибки при неверных типах данных в initial data."""
    data = [{"ID": 1, "name": 123}]  # name должен быть str
    with pytest.raises(TypeError):
        Table(name="test", columns=[("ID", "int"), ("name", "str")], data=data)


# ==================== Тесты Insert ====================


def test_insert_basic():
    """Тест базовой вставки."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    record = table.insert(["Alice"])

    assert record["ID"] == 1
    assert record["name"] == "Alice"
    assert len(table.data) == 1


def test_insert_auto_id_increment():
    """Тест автоинкремента ID."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])
    table.insert(["Bob"])

    assert table.data[0]["ID"] == 1
    assert table.data[1]["ID"] == 2


def test_insert_max_id_gap():
    """Тест генерации ID после удаления (max + 1)."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])  # ID 1
    table.insert(["Bob"])  # ID 2
    table.delete({"name": "Bob"})  # Удаляем Bob
    table.insert(["Charlie"])  # ID должен быть 2, т.к. максимальный ID теперь удалён

    assert table.data[-1]["ID"] == 2
    table.delete({"name": "Alice"})  # ID 1 удалён
    table.insert(["Kirk"])  # ID теперь должен быть 3
    assert table.data[-1]["ID"] == 3


def test_insert_wrong_count_values():
    """Тест вставки неверного количества значений."""
    table = Table(
        name="users", columns=[("ID", "int"), ("name", "str"), ("age", "int")]
    )
    with pytest.raises(ValueError):
        table.insert(["Alice"])  # Нужно 2 значения


def test_insert_wrong_types():
    """Тест вставки неверных типов."""
    table = Table(name="users", columns=[("ID", "int"), ("age", "int")])
    with pytest.raises(TypeError):
        table.insert(["twenty"])


def test_insert_immutability_of_input():
    """Тест что insert не меняет входной список values."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    values = ["Alice"]
    original_values = deepcopy(values)

    table.insert(values)

    assert values == original_values


# ==================== Тесты Select ====================


def test_select_all():
    """Тест выборки всех записей."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])
    table.insert(["Bob"])

    results = table.select()

    assert len(results) == 2


def test_select_where_match():
    """Тест выборки по условию."""
    table = Table(
        name="users", columns=[("ID", "int"), ("name", "str"), ("age", "int")]
    )
    table.insert(["Alice", 25])
    table.insert(["Bob", 30])

    results = table.select(where_clause={"age": 30})

    assert len(results) == 1
    assert results[0]["name"] == "Bob"


def test_select_no_match():
    """Тест выборки без совпадений."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])

    results = table.select(where_clause={"name": "Bob"})

    assert len(results) == 0


def test_select_copy_policy_do_copy():
    """Тест что select возвращает копии по умолчанию."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])

    results = table.select(do_copy=CopyPolicy.DO_COPY)
    results[0]["name"] = "Modified"

    assert table.data[0]["name"] == "Alice"


def test_select_copy_policy_do_not_copy():
    """Тест что select возвращает ссылки при DO_NOT_COPY."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])

    results = table.select(do_copy=CopyPolicy.DO_NOT_COPY)

    # Изменяем результат
    results[0]["name"] = "Modified"

    # Проверяем, что оригинал тоже изменился (так как это ссылка)
    assert table.data[0]["name"] == "Modified", (
        "При DO_NOT_COPY должна возвращаться ссылка!"
    )


def test_select_empty_table():
    """Тест выборки из пустой таблицы."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    results = table.select()
    assert results == []


# ==================== Тесты Update ====================


def test_update_single_record():
    """Тест обновления одной записи."""
    table = Table(
        name="users", columns=[("ID", "int"), ("name", "str"), ("age", "int")]
    )
    table.insert(["Alice", 25])
    table.insert(["Bob", 30])

    count = table.update(set_clause={"age": 31}, where_clause={"name": "Bob"})

    assert count == 1
    assert table.data[1]["age"] == 31


def test_update_multiple_records():
    """Тест обновления нескольких записей."""
    table = Table(name="users", columns=[("ID", "int"), ("city", "str")])
    table.insert(["Moscow"])
    table.insert(["Moscow"])

    count = table.update(set_clause={"city": "SPB"}, where_clause={"city": "Moscow"})

    assert count == 2
    assert all(r["city"] == "SPB" for r in table.data)


def test_update_nonexistent_column():
    """Тест обновления несуществующего столбца."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    with pytest.raises(KeyError):
        table.update(set_clause={"fake": "val"}, where_clause={"ID": 1})


def test_update_id_forbidden():
    """Тест запрета обновления ID."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])
    with pytest.raises(ValueError):
        table.update(set_clause={"ID": 999}, where_clause={"name": "Alice"})


def test_update_wrong_type():
    """Тест обновления неверным типом."""
    table = Table(name="users", columns=[("ID", "int"), ("age", "int")])
    table.insert([25])
    with pytest.raises(TypeError):
        table.update(set_clause={"age": "old"}, where_clause={"ID": 1})


def test_update_no_matches():
    """Тест обновления без совпадений."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])

    count = table.update(set_clause={"name": "Bob"}, where_clause={"name": "Charlie"})

    assert count == 0
    assert table.data[0]["name"] == "Alice"


# ==================== Тесты Delete ====================


def test_delete_single_record():
    """Тест удаления одной записи."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])
    table.insert(["Bob"])

    count = table.delete(where_clause={"name": "Alice"})

    assert count == 1
    assert len(table.data) == 1
    assert table.data[0]["name"] == "Bob"


def test_delete_multiple_records():
    """Тест удаления нескольких записей."""
    table = Table(name="users", columns=[("ID", "int"), ("status", "str")])
    table.insert(["active"])
    table.insert(["inactive"])
    table.insert(["active"])

    count = table.delete(where_clause={"status": "active"})

    assert count == 2
    assert len(table.data) == 1
    assert table.data[0]["status"] == "inactive"


def test_delete_no_matches():
    """Тест удаления без совпадений."""
    table = Table(name="users", columns=[("ID", "int"), ("name", "str")])
    table.insert(["Alice"])

    count = table.delete(where_clause={"name": "Bob"})

    assert count == 0
    assert len(table.data) == 1


def test_delete_all():
    """Тест удаления всех записей через условие.

    Так как where_clause обязателен, мы не можем сделать delete().
    Мы имитируем удаление всех, задавая условие, подходящее всем записям,
    или удаляя их последовательно.
    """
    table = Table(name="users", columns=[("ID", "int"), ("status", "str")])
    table.insert(["active"])
    table.insert(["active"])

    # Удаляем все записи со статусом 'active'
    count = table.delete(where_clause={"status": "active"})

    assert count == 2, "Должны быть удалены 2 записи"
    assert len(table.data) == 0, "Таблица должна быть пустой"


# ==================== Тесты Save/Load ====================


def test_save_and_load_table(tmp_path: Path):
    """Тест полного цикла сохранения и загрузки."""
    original_table = Table(name="products", columns=[("ID", "int"), ("title", "str")])
    original_table.insert(["Laptop"])
    original_table.insert(["Phone"])

    file_path = tmp_path / "data" / "products.json"

    Table.save_table(original_table, file_path)

    # Загружаем новую таблицу
    loaded_table = Table.load_table(
        file_path=str(file_path),
        table_name="products",
        columns=[("ID", "int"), ("title", "str")],
    )

    assert loaded_table.name == original_table.name
    assert loaded_table.columns == original_table.columns
    assert len(loaded_table.data) == len(original_table.data)
    assert loaded_table.data[0]["title"] == "Laptop"


def test_load_table_file_not_found():
    """Тест загрузки несуществующего файла."""
    with pytest.raises(FileNotFoundError):
        Table.load_table(
            file_path="/nonexistent/path.json",
            table_name="test",
            columns=[("ID", "int")],
        )


def test_load_table_invalid_columns():
    """Тест загрузки с неверной схемой."""
    with pytest.raises(TypeError):
        Table.load_table(file_path="dummy.json", table_name="test", columns="bad")


def test_save_table_creates_directory(tmp_path: Path):
    """Тест что save создает директорию."""
    table = Table(name="test", columns=[("ID", "int")])
    file_path = tmp_path / "new_dir" / "sub_dir" / "test.json"

    Table.save_table(table, file_path)

    assert file_path.exists()


def test_repr():
    """Тест строкового представления."""
    table = Table(name="users", columns=[("ID", "int")])
    table.insert([])

    repr_str = repr(table)

    assert "Table" in repr_str
    assert "users" in repr_str
    assert "records_count=1" in repr_str


def _setup_metadata_and_table(tmp_path: Path, table_name: str = "users"):
    """
    Корректно создает таблицу через core.create_table
    и сохраняет её начальный файл данных.
    Возвращает актуальные метаданные и путь к папке data.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)

    # Начальные пустые метаданные
    metadata = {}
    columns = [("name", "str"), ("age", "int")]

    # Используем официальную функцию создания из core.py
    # Она сама добавит ID, проверит структуру и вернет обновленный metadata с путем
    metadata = create_table(metadata, table_name, columns, data_path=str(data_dir))

    # Теперь создадим физический файл данных для этой таблицы,
    # используя путь из metadata
    table_path = metadata["tables"][table_name]["path"]
    initial_table = Table(
        name=table_name, columns=metadata["tables"][table_name]["columns"]
    )
    Table.save_table(initial_table, table_path)

    return metadata, str(data_dir)


def test_load_table_by_metadata_success(tmp_path: Path):
    """Тест успешной загрузки таблицы по метаданным."""
    metadata, data_path = _setup_metadata_and_table(tmp_path)

    # Проверяем, что файл действительно создан по пути из метаданных
    assert Path(metadata["tables"]["users"]["path"]).exists()

    table = Table.load_table_by_metadata(metadata, "users", data_path)

    assert table.name == "users"
    assert len(table.columns) == 3  # ID + name + age
    assert isinstance(table, Table)


def test_load_table_by_metadata_missing_table():
    """Тест ошибки при загрузке несуществующей таблицы."""
    metadata = {"tables": {}}

    with pytest.raises(Exception):  # TableIsMissingError
        Table.load_table_by_metadata(metadata, "nonexistent", "/tmp")


def test_load_table_by_metadata_missing_data_file(tmp_path: Path):
    """Тест ошибки если файл данных удален, но есть в метаданных."""
    metadata, data_path = _setup_metadata_and_table(tmp_path)

    # Удаляем файл данных, симулируя повреждение БД
    file_path = Path(metadata["tables"]["users"]["path"])
    if file_path.exists():
        file_path.unlink()

    with pytest.raises(Exception):  # TableIsMissingError
        Table.load_table_by_metadata(metadata, "users", data_path)


def test_save_table_by_metadata_success(tmp_path: Path):
    """Тест успешного сохранения таблицы по метаданным."""
    metadata, data_path = _setup_metadata_and_table(tmp_path)

    # Загружаем таблицу, меняем её и сохраняем обратно
    table = Table.load_table_by_metadata(metadata, "users", data_path)
    table.insert(["Bob", 25])

    Table.save_table_by_metadata(metadata, table, data_path)

    # Проверяем файл напрямую через повторную загрузку
    loaded_check = Table.load_table_by_metadata(metadata, "users", data_path)
    assert len(loaded_check.data) == 1
    assert loaded_check.data[0]["name"] == "Bob"
    assert loaded_check.data[0]["age"] == 25


def test_save_table_by_metadata_missing_table():
    """Тест ошибки сохранения несуществующей таблицы."""
    metadata = {"tables": {}}
    table = Table(name="fake", columns=[("ID", "int"), ("val", "str")])

    with pytest.raises(Exception):  # TableIsMissingError
        Table.save_table_by_metadata(metadata, table, "/tmp")
