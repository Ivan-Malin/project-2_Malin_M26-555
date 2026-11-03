"""Содержит основной цикл проекта по работе с базой данных."""

from primitive_db.constants import DB_COMMANDS, TABLES_METADATA_PATH
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    select,
    update,
)
from primitive_db.decorators import (
    check_user_input,
    confirm_action,
    handle_db_errors,
    log_time,
)
from primitive_db.parser import (
    parse_column_str,
    parse_insert_values,
    parse_set_clause,
    parse_where_clause,
)
from primitive_db.tables import Table
from primitive_db.user_interaction import (
    get_and_parse_user_args,
    print_err,
    print_help,
    print_no_command,
    print_success,
    print_table,
)
from primitive_db.utils import (
    OverwritePolicy,
    create_database_structure_if_none,
    load_metadata,
    save_metadata,
)


@handle_db_errors
@check_user_input(DB_COMMANDS["create_table"][0])
def create_table_by_args(command_args: list) -> None:
    """Создаёт таблицу по аргументам от пользователя.

    Args:
        command_args (list): пользовательский ввод

    """
    # Загружаем БД
    metadata = load_metadata(TABLES_METADATA_PATH)

    table_name = command_args[1]

    columns = [
        parse_column_str(column_str) for column_str in command_args[2].split(" ")
    ]

    metadata = create_table(metadata, table_name, columns)

    save_metadata(TABLES_METADATA_PATH, metadata)
    print_success(f"Таблица '{table_name}' успешно создана")


@confirm_action("удаление таблицы")
@handle_db_errors
@check_user_input(DB_COMMANDS["drop_table"][0])
def drop_table_by_args(command_args: list) -> None:
    """Удаляет таблицу по аргументам от пользователя.

    Args:
        command_args (list): пользовательский ввод

    """
    # Загружаем БД
    metadata = load_metadata(TABLES_METADATA_PATH)

    table_name = command_args[1]

    metadata = drop_table(metadata, table_name)

    save_metadata(TABLES_METADATA_PATH, metadata)
    print_success(f"Таблица '{table_name}' успешно удалена")


@handle_db_errors
@check_user_input(DB_COMMANDS["list_tables"][0])
def list_tables_by_args(command_args: list) -> None:
    """Выводит список всех таблиц на экран.

    Args:
        command_args (list): пользовательский ввод

    """
    # Загружаем таблицу
    metadata = load_metadata(TABLES_METADATA_PATH)

    table_names = [f'"{table_name}"' for table_name in metadata["tables"]]

    print(f"Список таблиц: {', '.join(table_names)}")


@log_time("insert")
@handle_db_errors
@check_user_input(DB_COMMANDS["insert"][0])
def insert_into_table_by_args(command_args: list) -> None:
    """Добавляет запись в таблицу по аргументам от пользователя.

    Args:
        command_args (list): пользовательский ввод

    """
    # Загружаем таблицу
    metadata = load_metadata(TABLES_METADATA_PATH)

    table_name = command_args[2]

    table = Table.load_table_by_metadata(metadata, table_name)

    # Вставляем данные в таблицу
    values = parse_insert_values(command_args[4])

    table_result = insert(table, values)
    Table.save_table_by_metadata(
        metadata,
        table_result,
        overwrite=OverwritePolicy.DO_OVERWRITE,
    )
    print_success(f"Данные успешно добавлены в таблицу {table_name}.")


@log_time("select")
@handle_db_errors
@check_user_input(DB_COMMANDS["select"][0])
def select_from_table_by_args(command_args: list) -> None:
    """Выбирает записи из таблицы по аргументам от пользователя.

    Поддерживает форматы:
    - select from <имя_таблицы>
    - select from <имя_таблицы> where <столбец> = <значение>

    Args:
        command_args (list): пользовательский ввод

    """
    # Загружаем метаданные
    metadata = load_metadata(TABLES_METADATA_PATH)

    table_name = command_args[2]

    # Загружаем таблицу
    table = Table.load_table_by_metadata(metadata, table_name)

    # Парсим where_clause
    if (
        len(command_args) > len(("select", "from", "table"))
        and command_args[3].lower() == "where"
    ):
        condition_str = command_args[4]

        where_clause = parse_where_clause(condition_str)
    else:
        where_clause = None

    # Выполняем select
    results = select(table, where_clause)

    # Выводим результат с помощью PrettyTable
    if not results:
        print("Записи не найдены.")
        return

    print_table(table, results)


@confirm_action("удаление записей")
@handle_db_errors
@check_user_input(DB_COMMANDS["delete"][0])
def delete_from_table_by_args(command_args: list) -> None:
    """Удаляет записи из таблицы по аргументам от пользователя.

    Поддерживает формат:
    - delete from <имя_таблицы> where <столбец> = <значение>

    Args:
        command_args (list): пользовательский ввод

    """
    # Загружаем метаданные
    metadata = load_metadata(TABLES_METADATA_PATH)

    table_name = command_args[2]

    # Загружаем таблицу
    table = Table.load_table_by_metadata(metadata, table_name)

    # Парсим where_clause
    if (
        len(command_args) > len(("delete", "from", "table"))
        and command_args[3].lower() == "where"
    ):
        condition_str = command_args[4]

        where_clause = parse_where_clause(condition_str)
    else:
        print_err("Для удаления записей необходимо указать условие where.")
        return

    # Выполняем удаление
    table_result, delete_count = delete(table, where_clause)

    # Сохраняем обновленную таблицу
    Table.save_table_by_metadata(
        metadata,
        table_result,
        overwrite=OverwritePolicy.DO_OVERWRITE,
    )

    print_success(f"Удалено записей: {delete_count} из таблицы '{table_name}'.")


@handle_db_errors
@check_user_input(DB_COMMANDS["update"][0])
def update_table_by_args(command_args: list) -> None:
    """Обновляет записи в таблице по аргументам от пользователя.

    Поддерживает формат:
    - update <имя_таблицы> set <столбец> = <значение> where <столбец> = <значение>

    Args:
        command_args (list): пользовательский ввод

    """
    # Загружаем метаданные
    metadata = load_metadata(TABLES_METADATA_PATH)

    table_name = command_args[1]

    # Загружаем таблицу
    table = Table.load_table_by_metadata(metadata, table_name)

    # Парсим set и where
    set_clause = parse_set_clause(command_args[3])
    where_clause = parse_where_clause(command_args[5])

    # Выполняем обновление
    table_result, update_count = update(table, set_clause, where_clause)

    Table.save_table_by_metadata(
        metadata,
        table_result,
        overwrite=OverwritePolicy.DO_OVERWRITE,
    )

    print_success(
        f"Записи в таблице '{table_name}' успешно обновлены. "
        f"Затронуто {update_count} записей.",
    )


@handle_db_errors
@check_user_input(DB_COMMANDS["info"][0])
def info_from_table_by_args(command_args: list) -> None:
    """Выводит информацию о таблице по аргументам от пользователя.

    Поддерживает формат:
    - info <имя_таблицы>

    Args:
        command_args (list): пользовательский ввод

    """
    # Загружаем метаданные
    metadata = load_metadata(TABLES_METADATA_PATH)

    table_name = command_args[1]

    # Загружаем таблицу для получения актуальных данных и схемы
    table = Table.load_table_by_metadata(metadata, table_name)

    # Формируем данные
    columns_str = ", ".join([f"{name}:{dtype}" for name, dtype in table.columns])
    records_count = len(table.data)

    # Выводим информацию
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {columns_str}")
    print(f"Количество записей: {records_count}")


def run() -> None:
    """Основной цикл программы."""
    print_help()

    # Подготавливаем директорию целевую директорию под БД
    create_database_structure_if_none(TABLES_METADATA_PATH)

    while True:
        # Получаем ввод от пользователя
        command_args = get_and_parse_user_args()

        command_name = command_args[0]

        match command_name:
            case "create_table":
                create_table_by_args(command_args)
            case "drop_table":
                drop_table_by_args(command_args)
            case "list_tables":
                list_tables_by_args(command_args)
            case "insert":
                insert_into_table_by_args(command_args)
            case "select":
                select_from_table_by_args(command_args)
            case "delete":
                delete_from_table_by_args(command_args)
            case "update":
                update_table_by_args(command_args)
            case "info":
                info_from_table_by_args(command_args)
            case "help":
                print_help()
            case "exit":
                break
            case _:
                print_no_command()
