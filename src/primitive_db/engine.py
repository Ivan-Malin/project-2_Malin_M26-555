"""Содержит основной цикл проекта по работе с базой данных."""

import shlex
from collections.abc import Sequence

import prompt
from prettytable import PrettyTable

from primitive_db.constants import HELP_TEXT, TABLES_METADATA_PATH
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    parse_column_str,
    select,
    update,
)
from primitive_db.errors import TableAlreadyExistsError, TableIsMissingError
from primitive_db.parser import (
    parse_insert_values,
    parse_set_clause,
    parse_where_clause,
)
from primitive_db.tables import Table
from primitive_db.utils import (
    OverwritePolicy,
    create_database_structure_if_none,
    load_metadata,
    save_metadata,
)


def print_help() -> None:
    """Выводит вспомогательное сообщение с описанием пользовательского интерфейса."""
    print(HELP_TEXT)


def print_user_input_error() -> None:
    """Пишет ошибку о некорректном вводе для пользователя."""
    print("Некорректный ввод. Повторите свою команду.")
    print("\n")


def print_no_command() -> None:
    """Пишет ошибку об отсутствии команды для пользователя."""
    print("Ошибка. Команда не реализована.")
    print("\n")


def print_err(err: str = "") -> None:
    """Пишет ошибку о неправильных аргументах для пользователя.

    Args:
        err (str, optional): Кастомное название ошибки. По умолчанию "".

    """
    err_str = ""
    if err:
        err_str = f"Ошибка: {err}"

    print(f"Неправильно заданы аргументы команды. {err_str}")
    print("\n")


def print_success(result: str = "") -> None:
    """Пишет успешный результат выполнения команды для пользователя.

    Args:
        result (str, optional): результат выполнения. По умолчанию "".

    """
    print("Успех. ", end="")
    if result:
        print(f"{result}")
    print("\n")


def print_table(table: Table, records: list[dict] | None = None) -> None:
    """Выводит форматированную таблицу в консоль.

    Args:
        table (Table): исходная таблица
        records (list[dict], optional): список записей.
            Если None, то берёт записи из таблицы.
            По умолчанию None.

    """
    if records is None:
        records = table.data

    # Создаем таблицу для красивого вывода
    pt = PrettyTable()

    # Добавляем заголовки столбцов из схемы таблицы
    headers = [col[0] for col in table.columns]
    pt.field_names = headers

    # Добавляем данные
    for record in records:
        row = [record.get(col_name, "") for col_name in headers]
        pt.add_row(row)

    print(pt)


def get_user_command_line() -> str:
    """Welcome-функция, получающая ввод пользователя.

    Returns:
        str: название команды

    """
    return prompt.string(">>> Введите команду: ")


def get_and_parse_user_args() -> str:
    """Welcome-функция, получающая и декодирующая ввод пользователя.

    Returns:
        args: аргументы

    """
    command_line = get_user_command_line()
    command_args = None

    while not command_args:
        try:
            command_args = shlex.split(command_line)
        except ValueError:
            print_user_input_error()
            command_args = None
            continue

        if len(command_args) == 0:
            print_user_input_error()
            command_args = None
            continue

    return command_args


def create_table_by_args(command_args: list) -> None:
    """Создаёт таблицу по аргументам от пользователя.

    Args:
        command_args (list): пользовательский ввод

    """
    if not isinstance(command_args, Sequence):
        msg = "command_args не является списком аргументов"
        raise TypeError(msg)

    # Загружаем БД
    metadata = load_metadata(TABLES_METADATA_PATH)

    try:
        table_name = command_args[1]
    except IndexError:
        print_err("Недостаточно аргмуентов")
        return

    try:
        columns = [parse_column_str(column_str) for column_str in command_args[2:]]
    except (IndexError, KeyError, ValueError, TypeError) as err:
        print_err(err)
        return

    try:
        metadata = create_table(metadata, table_name, columns)
    except (TypeError, ValueError, TableAlreadyExistsError) as err:
        print_err(err)
        return

    save_metadata(TABLES_METADATA_PATH, metadata)
    print_success(f"Таблица '{table_name}' успешно создана")


def drop_table_by_args(command_args: list) -> None:
    """Удаляет таблицу по аргументам от пользователя.

    Args:
        command_args (list): пользовательский ввод

    """
    if not isinstance(command_args, Sequence):
        msg = "command_args не является списком аргументов"
        raise TypeError(msg)

    # Загружаем БД
    metadata = load_metadata(TABLES_METADATA_PATH)

    try:
        table_name = command_args[1]
    except IndexError:
        print_err("Недостаточно аргмуентов")
        return

    try:
        metadata = drop_table(metadata, table_name)
    except KeyError as err:
        print_err(err)
        return

    save_metadata(TABLES_METADATA_PATH, metadata)
    print_success(f"Таблица '{table_name}' успешно удалена")


def insert_into_table_by_args(command_args: list) -> None:
    """Добавляет запись в таблицу по аргументам от пользователя.

    Args:
        command_args (list): пользовательский ввод

    """
    if not isinstance(command_args, Sequence):
        msg = "command_args не является списком аргументов"
        raise TypeError(msg)

    # Загружаем таблицу
    metadata = load_metadata(TABLES_METADATA_PATH)

    try:
        table_name = command_args[2]
    except IndexError:
        print_err("Недостаточно аргмуентов")
        return

    try:
        table = Table.load_table_by_metadata(metadata, table_name)
    except TableIsMissingError as err:
        print_err(err)
        return

    # Вставляем данные в таблицу
    try:
        values = parse_insert_values(" ".join(command_args[4:]))
    except IndexError as err:
        print_err(f"Недостаточно аргмуентов. {err}")
        return
    except (ValueError, TypeError) as err:
        print_err(f"Некорректные аргументы. {err}")
        return

    try:
        table_result = insert(table, values)
        Table.save_table_by_metadata(
            metadata,
            table_result,
            overwrite=OverwritePolicy.DO_OVERWRITE,
        )
        print_success(f"Данные успешно добавлены в таблицу {table_name}.")
    except (TypeError, ValueError) as err:
        print_err(f"{err}")
        return


def select_from_table_by_args(command_args: list) -> None:
    """Выбирает записи из таблицы по аргументам от пользователя.

    Поддерживает форматы:
    - select from <имя_таблицы>
    - select from <имя_таблицы> where <столбец> = <значение>

    Args:
        command_args (list): пользовательский ввод

    """
    if not isinstance(command_args, Sequence):
        msg = "command_args не является списком аргументов"
        raise TypeError(msg)

    # Загружаем метаданные
    metadata = load_metadata(TABLES_METADATA_PATH)

    try:
        table_name = command_args[2]
    except IndexError:
        print_err("Недостаточно аргументов. Пример: select from users")
        return

    # Загружаем таблицу
    try:
        table = Table.load_table_by_metadata(metadata, table_name)
    except TableAlreadyExistsError as err:
        print_err(err)
        return

    # Парсим where_clause
    if (
        len(command_args) > len(("select", "from", "table"))
        and command_args[3].lower() == "where"
    ):
        condition_str = " ".join(command_args[4:])

        try:
            where_clause = parse_where_clause(condition_str)
        except (ValueError, TypeError) as err:
            print_err(f"Ошибка в условии where: {err}")
            return
    else:
        where_clause = None

    # Выполняем select
    try:
        results = select(table, where_clause)
    except ValueError as err:
        print_err(err)
        return

    # Выводим результат с помощью PrettyTable
    if not results:
        print("Записи не найдены.")
        return

    print_table(table, results)


def delete_from_table_by_args(command_args: list) -> None:
    """Удаляет записи из таблицы по аргументам от пользователя.

    Поддерживает формат:
    - delete from <имя_таблицы> where <столбец> = <значение>

    Args:
        command_args (list): пользовательский ввод

    """
    if not isinstance(command_args, Sequence):
        msg = "command_args не является списком аргументов"
        raise TypeError(msg)

    # Загружаем метаданные
    metadata = load_metadata(TABLES_METADATA_PATH)

    try:
        table_name = command_args[2]
    except IndexError:
        print_err("Недостаточно аргументов. Пример: delete from users where id = 1")
        return

    # Загружаем таблицу
    try:
        table = Table.load_table_by_metadata(metadata, table_name)
    except TableAlreadyExistsError as err:
        print_err(err)
        return

    # Парсим where_clause
    if (
        len(command_args) > len(("delete", "from", "table"))
        and command_args[3].lower() == "where"
    ):
        condition_str = " ".join(command_args[4:])

        try:
            where_clause = parse_where_clause(condition_str)
        except (ValueError, TypeError) as err:
            print_err(f"Ошибка в условии where: {err}")
            return
    else:
        print_err("Для удаления записей необходимо указать условие where.")
        return

    # Выполняем удаление
    try:
        table_result = delete(table, where_clause)

        # Сохраняем обновленную таблицу
        Table.save_table_by_metadata(
            metadata,
            table_result,
            overwrite=OverwritePolicy.DO_OVERWRITE,
        )

        deleted_count = len(table.data) - len(table_result.data)
        print_success(f"Удалено записей: {deleted_count} из таблицы '{table_name}'.")

    except (KeyError, ValueError, TypeError, TableIsMissingError) as err:
        print_err(f"Ошибка при удалении: {err}")
        return


def update_table_by_args(command_args: list) -> None:
    """Обновляет записи в таблице по аргументам от пользователя.

    Поддерживает формат:
    - update <имя_таблицы> set <столбец> = <значение> where <столбец> = <значение>

    Args:
        command_args (list): пользовательский ввод

    """
    if not isinstance(command_args, Sequence):
        msg = "command_args не является списком аргументов"
        raise TypeError(msg)

    # Загружаем метаданные
    metadata = load_metadata(TABLES_METADATA_PATH)

    try:
        table_name = command_args[1]
    except IndexError:
        print_err(
            "Недостаточно аргументов. Пример: "
            "update users set age = 30 where name = Ivan",
        )
        return

    # Загружаем таблицу
    try:
        table = Table.load_table_by_metadata(metadata, table_name)
    except TableAlreadyExistsError as err:
        print_err(err)
        return

    # Предварительно парсим set и where.
    set_index = None
    where_index = None

    for i, arg in enumerate(command_args):
        if arg.lower() == "set":
            set_index = i
        elif arg.lower() == "where":
            where_index = i

    if set_index is None or where_index is None:
        print_err("Отсутствуют нужные ключевые слова.")
        return

    set_parts = command_args[set_index + 1 : where_index]
    where_parts = command_args[where_index + 1 :]

    if not set_parts or not where_parts:
        print_err("Неверно заданы аргументы 'set' или 'where'.")
        return

    # Парсим set и where
    try:
        set_str = " ".join(set_parts)
        where_str = " ".join(where_parts)

        set_clause = parse_set_clause(set_str)
        where_clause = parse_where_clause(where_str)

    except (ValueError, TypeError) as err:
        print_err(f"Ошибка в синтаксисе команды: {err}")
        return

    # Выполняем обновление
    try:
        table_result = update(table, set_clause, where_clause)

        Table.save_table_by_metadata(
            metadata,
            table_result,
            overwrite=OverwritePolicy.DO_OVERWRITE,
        )

        updated_len = len(table.data) - len(table_result.data)
        print_success(
            f"Записи в таблице '{table_name}' успешно обновлены."
            f"Затронуто {updated_len} записей.",
        )

    except (KeyError, ValueError, TypeError, TableIsMissingError) as err:
        print_err(f"Ошибка при обновлении: {err}")
        return


def info_from_table_by_args(command_args: list) -> None:
    """Выводит информацию о таблице по аргументам от пользователя.

    Поддерживает формат:
    - info <имя_таблицы>

    Args:
        command_args (list): пользовательский ввод

    """
    if not isinstance(command_args, Sequence):
        msg = "command_args не является списком аргументов"
        raise TypeError(msg)

    # Загружаем метаданные
    metadata = load_metadata(TABLES_METADATA_PATH)

    try:
        table_name = command_args[1]
    except IndexError:
        print_err("Недостаточно аргументов. Пример: info users")
        return

    # Загружаем таблицу для получения актуальных данных и схемы
    try:
        table = Table.load_table_by_metadata(metadata, table_name)
    except TableAlreadyExistsError as err:
        print_err(err)
        return

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
