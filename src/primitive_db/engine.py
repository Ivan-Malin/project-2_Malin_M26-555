"""Содержит запуск, игровой цикл и парсинг команд."""

import shlex

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
    print("\n")
    print("------------------------------------------")
    print("Некорректный ввод. Повторите свою команду.")
    print("------------------------------------------")


def print_no_command() -> None:
    """Пишет ошибку об отсутствии команды для пользователя."""
    print("\n")
    print("------------------------------------------")
    print("Команда не реализована.")
    print("------------------------------------------")


def print_bad_args(err: str = "") -> None:
    """Пишет ошибку о неправильных аргументах для пользователя.

    Args:
        err (str, optional): Кастомное название ошибки. По умолчанию "".

    """
    err_str = ""
    if err:
        err_str = f"Ошибка: {err}"

    print("\n")
    print("------------------------------------------")
    print(f"Неправильно заданы аргументы команды. {err_str}")
    print("------------------------------------------")


def print_success(result: str = "") -> None:
    """Пишет успешный результат выполнения команды для пользователя.

    Args:
        result (str, optional): результат выполнения. По умолчанию "".

    """
    print("\n")
    print("------------------------------------------")
    print("Команда успешно выполнена.")
    if result:
        print(f"{result}")
    print("------------------------------------------")


def get_user_command_line() -> str:
    """Welcome-функция, получающая ввод пользователя.

    Returns:
        str: название команды

    """
    print_help()
    return prompt.string("Введите команду: ")


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


def run() -> None:
    """Основной цикл программы."""
    while True:
        # Загружаем таблицы
        metadata = load_metadata(TABLES_METADATA_PATH)

        # Получаем ввод от пользователя
        command_args = get_and_parse_user_args()

        command_name = command_args[0]

        match command_name:
            case "create_table":
                try:
                    table_name = command_args[1]
                except IndexError:
                    print_bad_args("Недостаточно аргмуентов")
                    continue

                try:
                    columns = [
                        parse_column_str(column_str) for column_str in command_args[2:]
                    ]
                except (IndexError, KeyError, ValueError, TypeError) as err:
                    print_bad_args(err)
                    continue

                try:
                    metadata = create_table(metadata, table_name, columns)
                except (TypeError, ValueError) as err:
                    print_bad_args(err)
                    continue

                save_metadata(TABLES_METADATA_PATH, metadata)
                print_success(f"Таблица '{table_name}' успешно создана")
            case "drop_table":
                try:
                    table_name = command_args[1]
                except IndexError:
                    print_bad_args("Недостаточно аргмуентов")
                    continue

                try:
                    metadata = drop_table(metadata, table_name)
                except KeyError as err:
                    print_bad_args(err)
                    continue

                save_metadata(TABLES_METADATA_PATH, metadata)
                print_success(f"Таблица '{table_name}' успешно удалена")
            case _:
                print_no_command()
