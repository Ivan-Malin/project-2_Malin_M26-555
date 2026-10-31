"""Содержит основной цикл проекта по работе с базой данных."""

import shlex
from collections.abc import Sequence

import prompt

from primitive_db.core import create_table, drop_table, parse_column_str
from primitive_db.utils import get_current_path, load_metadata, save_metadata

TABLES_METADATA_PATH = f"{get_current_path()}/db_meta.json"


def print_help() -> None:
    """Print the help message for the current mode."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


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
    except (TypeError, ValueError) as err:
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


def run() -> None:
    """Основной цикл программы."""
    print_help()
    while True:
        # Получаем ввод от пользователя
        command_args = get_and_parse_user_args()

        command_name = command_args[0]

        match command_name:
            case "create_table":
                create_table_by_args(command_args)
            case "drop_table":
                drop_table_by_args(command_args)
            case "help":
                print_help()
            case "exit":
                break
            case _:
                print_no_command()
