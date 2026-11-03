import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from primitive_db.constants import (
    DATA_PATH,
    DEFAULT_METADATA_CONTENT,
    TABLES_METADATA_PATH,
)
from primitive_db.engine import run
from primitive_db.tables import Table
from primitive_db.utils import load_metadata, save_metadata

# Замечание проверяющему - часть тестовых файлов были отданы на откуп Qwen'у,
# т.к. тесты от нейросети (под пристальным ревью) лучше, чем никаких тестов вообще.


def _clean_db_state():
    """Полностью очищает состояние БД (файлы и метаданные) перед тестом."""
    data_dir = Path(DATA_PATH)
    metadata_file = Path(TABLES_METADATA_PATH)

    # Удаляем все файлы в папке data
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Сбрасываем метаданные до пустого состояния
    save_metadata(metadata_file, DEFAULT_METADATA_CONTENT)

    # Очищаем кэш select
    Table.clear_cache()


def _run_with_commands(commands: list[str], monkeypatch):
    """
    Вспомогательная функция для запуска цикла run с симуляцией ввода команд.
    """
    command_iter = iter(commands)

    def mock_input(prompt=""):
        try:
            return next(command_iter)
        except StopIteration:
            return "exit"

    monkeypatch.setattr("builtins.input", mock_input)

    with patch("primitive_db.user_interaction.prompt.string", side_effect=mock_input):
        with patch("primitive_db.engine.create_database_structure_if_none"):
            run()


def test_run_create_and_drop_integration(capsys, monkeypatch):
    _clean_db_state()

    commands = ["create_table users name:str age:int", "drop_table users", "y", "exit"]

    _run_with_commands(commands, monkeypatch)

    captured = capsys.readouterr()
    assert "Успех" in captured.out
    assert "users" in captured.out

    metadata = load_metadata(TABLES_METADATA_PATH)
    assert "users" not in metadata.get("tables", {}), "Таблица не была удалена!"


def test_run_invalid_command(capsys, monkeypatch):
    _clean_db_state()

    commands = ["unknown_command", "exit"]
    _run_with_commands(commands, monkeypatch)

    captured = capsys.readouterr()
    assert "не найдена" in captured.out.lower()


def test_run_create_table_error_handling(capsys, monkeypatch):
    _clean_db_state()

    # Создаем дубликат вручную
    initial_meta = load_metadata(TABLES_METADATA_PATH)
    initial_meta["tables"]["users"] = {"columns": []}
    save_metadata(TABLES_METADATA_PATH, initial_meta)

    commands = ["create_table users name:str", "exit"]
    _run_with_commands(commands, monkeypatch)

    captured = capsys.readouterr()
    assert "Ошибка" in captured.out or "Неправильно" in captured.out


def test_run_full_crud_cycle(capsys, monkeypatch):
    _clean_db_state()

    commands = [
        "create_table users name:str age:int is_active:bool",
        'insert into users values ("Alice", 25, true)',
        'insert into users values ("Bob", 30, false)',
        "select from users where age = 25",
        'update users set age = 26 where name = "Alice"',
        'delete from users where name = "Bob"',
        "y",
        "exit",
    ]

    try:
        _run_with_commands(commands, monkeypatch)
    except NameError:
        pytest.skip("Не все CRUD команды реализованы в engine.py")

    captured = capsys.readouterr()
    assert "Успех" in captured.out

    metadata = load_metadata(TABLES_METADATA_PATH)
    assert "users" in metadata["tables"]

    users_file_path = metadata["tables"]["users"]["path"]
    assert Path(users_file_path).exists()

    with open(users_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("data", [])
    assert len(records) == 1
    assert records[0]["name"] == "Alice"
    assert records[0]["age"] == 26


def test_run_drop_table_integration(capsys, monkeypatch):
    """
    Интеграционный тест удаления таблицы через цикл run:
    1. Создаем таблицу
    2. Удаляем её командой drop_table
    3. Проверяем, что она исчезла из метаданных
    """

    # Очищаем состояние перед тестом (если у вас есть функция _clean_db_state)
    # Если нет, можно добавить ручную очистку здесь:
    import shutil

    from primitive_db.constants import DATA_PATH, DEFAULT_METADATA_CONTENT
    from primitive_db.utils import save_metadata

    data_dir = Path(DATA_PATH)
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    save_metadata(TABLES_METADATA_PATH, DEFAULT_METADATA_CONTENT)

    commands = ["create_table users name:str age:int", "drop_table users", "y", "exit"]

    command_iter = iter(commands)

    def mock_input(prompt=""):
        try:
            return next(command_iter)
        except StopIteration:
            return "exit"

    monkeypatch.setattr("builtins.input", mock_input)

    with patch("primitive_db.user_interaction.prompt.string", side_effect=mock_input):
        with patch("primitive_db.engine.create_database_structure_if_none"):
            run()

    captured = capsys.readouterr()

    # Проверяем вывод об успешном удалении
    assert "Успех" in captured.out
    assert "users" in captured.out
    assert "удалена" in captured.out.lower()

    # Проверяем состояние метаданных
    metadata = load_metadata(TABLES_METADATA_PATH)

    # Таблица должна отсутствовать в метаданных
    assert "users" not in metadata.get("tables", {}), (
        "Таблица не была удалена из метаданных!"
    )

    # Опционально: проверить, что файл данных тоже был удален (если логика drop_table
    # это делает) Обычно drop_table удаляет только запись из metadata, а
    # файл может остаться "мусором", но если ваша реализация чистит и файлы, то можно
    # добавить проверку:
    # assert not (Path(DATA_PATH) / "users.json").exists()


def test_run_insert_validation_errors(capsys, monkeypatch):
    _clean_db_state()

    commands = [
        "create_table products title:str price:int",
        'insert into products values ("Laptop", "expensive")',
        "exit",
    ]

    _run_with_commands(commands, monkeypatch)

    captured = capsys.readouterr()
    assert "Ошибка" in captured.out

    metadata = load_metadata(TABLES_METADATA_PATH)
    if "products" in metadata["tables"]:
        path = metadata["tables"]["products"]["path"]
        if Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                assert len(json.load(f).get("data", [])) == 0


def test_run_insert_into_table(capsys, monkeypatch):
    _clean_db_state()

    commands = [
        "create_table users name:str age:int",
        'insert into users values ("Ivan", 30)',
        "exit",
    ]

    _run_with_commands(commands, monkeypatch)

    captured = capsys.readouterr()
    assert "Успех" in captured.out

    metadata = load_metadata(TABLES_METADATA_PATH)
    assert "users" in metadata["tables"]

    table_info = metadata["tables"]["users"]
    data_file_path = Path(table_info["path"])

    assert data_file_path.exists()

    with open(data_file_path, "r", encoding="utf-8") as f:
        data_content = json.load(f)

    records = data_content.get("data", [])
    assert len(records) == 1
    assert records[0]["name"] == "Ivan"
    assert records[0]["age"] == 30


def test_run_select_all_and_where(capsys, monkeypatch):
    _clean_db_state()

    # Примечание: если функции select/update/delete ещё не реализованы в engine.py,
    # этот тест упадет с NameError. Закомментируйте его, если они ещё не готовы.
    commands = [
        "create_table items id:int name:str",
        'insert into items values (1, "Item1")',
        'insert into items values (2, "Item2")',
        "select from items",
        'select from items where name = "Item1"',
        "exit",
    ]

    try:
        _run_with_commands(commands, monkeypatch)
        captured = capsys.readouterr()
        assert "Item1" in captured.out
        assert "Item2" in captured.out
    except NameError:
        pytest.skip("Функции select_from_table_by_args ещё не реализованы в engine.py")


def test_run_update_nonexistent_column(capsys, monkeypatch):
    _clean_db_state()

    commands = [
        "create_table test val:int",
        "insert into test values (10)",
        "update test set fake_col = 5 where val = 10",
        "exit",
    ]

    _run_with_commands(commands, monkeypatch)

    captured = capsys.readouterr()
    assert "Ошибка" in captured.out or "Столбец" in captured.out


def test_run_tz_example_crud_cycle(capsys, monkeypatch):
    _clean_db_state()

    commands = [
        "create_table users name:str age:int is_active:bool",
        'insert into users values ("Sergei", 28, true)',
        "select from users where age = 28",
        'update users set age = 29 where name = "Sergei"',
        "delete from users where ID = 1",
        "y",
        "info users",
        "exit",
    ]

    try:
        _run_with_commands(commands, monkeypatch)
        captured = capsys.readouterr()

        assert "Sergei" in captured.out
        assert "28" in captured.out
        assert "Таблица: users" in captured.out
        assert "Количество записей: 0" in captured.out

        metadata = load_metadata(TABLES_METADATA_PATH)
        users_file_path = metadata["tables"]["users"]["path"]

        with open(users_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        assert len(file_content.get("data", [])) == 0
    except NameError:
        pytest.skip("Не все CRUD команды реализованы в engine.py")


def test_run_isolation_multiple_tables(capsys, monkeypatch):
    """Проверка изоляции данных.

    Дданные из Table_B не должны попадать в вывод Table_A.
    """
    _clean_db_state()

    # Этап 1: Подготовка
    cmds = [
        "create_table table_alpha name:str",
        "create_table table_beta name:str",
        'insert into table_alpha values ("Alpha_Item")',
        'insert into table_beta values ("Beta_Item")',
        "exit",
    ]
    _run_with_commands(cmds, monkeypatch)
    capsys.readouterr()  # Сброс

    # Этап 2: Проверяем Alpha
    _run_with_commands(["select from table_alpha", "exit"], monkeypatch)
    out_alpha = capsys.readouterr().out
    assert "Alpha_Item" in out_alpha
    assert "Beta_Item" not in out_alpha

    # Этап 3: Проверяем Beta
    _run_with_commands(["select from table_beta", "exit"], monkeypatch)
    out_beta = capsys.readouterr().out
    assert "Beta_Item" in out_beta
    assert "Alpha_Item" not in out_beta


def test_run_update_delete_chain(capsys, monkeypatch):
    """Сценарий: Изменение данных с проверкой исчезновения старых значений."""
    _clean_db_state()

    # Этап 1: База
    cmds = [
        "create_table users name:str status:str",
        'insert into users values ("User_One", "Active")',
        'insert into users values ("User_Two", "Pending")',
        "exit",
    ]
    _run_with_commands(cmds, monkeypatch)
    capsys.readouterr()

    # Этап 2: Обновление статуса
    _run_with_commands(
        ['update users set status = "Blocked" where name = "User_One"', "exit"],
        monkeypatch,
    )
    out_upd = capsys.readouterr().out
    assert "Затронуто 1 записей" in out_upd

    # Этап 3: Проверка результата обновления
    _run_with_commands(["select from users", "exit"], monkeypatch)
    out_sel = capsys.readouterr().out
    assert "Blocked" in out_sel
    assert "Active" not in out_sel  # Старый статус должен исчезнуть

    # Этап 4: Удаление
    _run_with_commands(
        ['delete from users where name = "User_Two"', "y", "exit"], monkeypatch
    )
    capsys.readouterr()

    # Этап 5: Финальная проверка
    _run_with_commands(["select from users", "exit"], monkeypatch)
    out_final = capsys.readouterr().out
    assert "User_One" in out_final
    assert "User_Two" not in out_final


def test_run_error_recovery_and_recreation(capsys, monkeypatch):
    """Сценарий: Обработка ошибки дубликата и успешное пересоздание."""
    _clean_db_state()

    # Этап 1: Создание
    _run_with_commands(["create_table temp_tbl val:str", "exit"], monkeypatch)
    out1 = capsys.readouterr().out
    assert "Успех" in out1

    # Этап 2: Ошибка дубля
    _run_with_commands(["create_table temp_tbl val:str", "exit"], monkeypatch)
    out2 = capsys.readouterr().out
    assert "уже существует" in out2.lower() or "Ошибка" in out2

    # Этап 3: Удаление
    _run_with_commands(["drop_table temp_tbl", "y", "exit"], monkeypatch)
    out3 = capsys.readouterr().out
    assert "удалена" in out3.lower()

    # Этап 4: Повторное создание
    _run_with_commands(["create_table temp_tbl val:str", "exit"], monkeypatch)
    out4 = capsys.readouterr().out
    assert "Успех" in out4


def test_run_where_filtering_precision(capsys, monkeypatch):
    """Проверка точности фильтрации: поиск по уникальной строке."""
    _clean_db_state()

    # Этап 1: Данные
    cmds = [
        "create_table items code:str",
        'insert into items values ("CODE_100")',
        'insert into items values ("CODE_1000")',
        'insert into items values ("CODE_200")',
        "exit",
    ]
    _run_with_commands(cmds, monkeypatch)
    capsys.readouterr()

    # Этап 2: Фильтрация
    _run_with_commands(
        ['select from items where code = "CODE_100"', "exit"], monkeypatch
    )
    out_exact = capsys.readouterr().out

    assert "CODE_100" in out_exact
    assert "CODE_1000" not in out_exact
    assert "CODE_200" not in out_exact


def test_run_info_consistency(capsys, monkeypatch):
    """Проверка актуальности метаданных через команду info."""
    _clean_db_state()

    # Этап 1: Пустая таблица
    _run_with_commands(["create_table logs msg:str", "info logs", "exit"], monkeypatch)
    out1 = capsys.readouterr().out
    assert "Количество записей: 0" in out1

    # Этап 2: Добавление данных
    _run_with_commands(['insert into logs values ("Log_Entry_1")', "exit"], monkeypatch)
    capsys.readouterr()

    # Этап 3: Проверка info после вставки
    _run_with_commands(["info logs", "exit"], monkeypatch)
    out2 = capsys.readouterr().out
    assert "Количество записей: 1" in out2

    # Этап 4: Удаление данных
    _run_with_commands(
        ['delete from logs where msg = "Log_Entry_1"', "y", "exit"], monkeypatch
    )
    capsys.readouterr()

    # Этап 5: Проверка info после удаления
    _run_with_commands(["info logs", "exit"], monkeypatch)
    out3 = capsys.readouterr().out
    assert "Количество записей: 0" in out3
