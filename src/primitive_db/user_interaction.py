"""Содержит функции по взаимодействию с пользователем."""

import prompt  # Заброшенная отвратительная библиотека. Но нужна по ТЗ...
from prettytable import PrettyTable

from primitive_db.constants import DB_COMMANDS, GENERAL_COMMANDS
from primitive_db.parser import tokenize_user_args
from primitive_db.tables import Table


def get_user_command_line() -> str:
    """Welcome-функция, получающая ввод пользователя.

    Returns:
        str: название команды

    """
    return prompt.string("\n>>> Введите команду: ")


def get_and_parse_user_args() -> list[str]:
    """Welcome-функция, получающая и декодирующая ввод пользователя.

    Returns:
        args (list[str]): аргументы

    """
    command_args = None

    while not command_args:
        command_line = get_user_command_line()
        try:
            # ВАЖНО!!! shlex.split не умел работать с кавычками
            # внутри скобок, поэтому был заменён на обычный split(' ')
            # у которого в контексте текущей задачи нет недостатков
            command_args = command_line.split(" ")
        except ValueError:
            print_user_input_error()
            command_args = None
            continue

        if len(command_args) == 0:
            print_user_input_error()
            command_args = None
            continue

    return tokenize_user_args(command_args)


def ask_confirmation(action_name: str = "") -> None:
    """Пишет запрос на подтверждения действия.

    Args:
        action_name (str, optional): Название действия. Defaults to "".

    """
    if action_name is None:
        action_name = "действие"

    result = prompt.string(
        f'>> Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ',
    )

    return result.lower().replace(" ", "") == "y"


def print_help() -> None:
    """Выводит вспомогательное сообщение с описанием пользовательского интерфейса."""

    def format_commands(commands_dict: dict) -> list[str]:
        """Генерирует строки справки из словаря команд."""
        for formats, description in commands_dict.values():
            # Берем первый доступный формат для отображения
            primary_format = next(iter(formats))
            yield f"<command> {' '.join(primary_format)} - {description}"

    lines = [
        "***Процесс работы с таблицей***",
        "Функции:",
        *format_commands(DB_COMMANDS),
        "",
        "Общие команды:",
        *format_commands(GENERAL_COMMANDS),
        "",
    ]

    print("\n".join(lines))


def print_user_input_error() -> None:
    """Пишет ошибку о некорректном вводе для пользователя."""
    print("Некорректный ввод. Повторите свою команду.")


def print_no_command() -> None:
    """Пишет ошибку об отсутствии команды для пользователя."""
    print("Ошибка. Команда не найдена.")


def print_err(err: str = "") -> None:
    """Пишет ошибку о неправильных аргументах для пользователя.

    Args:
        err (str, optional): Кастомное название ошибки. По умолчанию "".

    """
    err_str = ""
    if err:
        err_str = f"Ошибка: {err}"

    print(f"Неправильно заданы аргументы команды. {err_str}")


def print_success(result: str = "") -> None:
    """Пишет успешный результат выполнения команды для пользователя.

    Args:
        result (str, optional): результат выполнения. По умолчанию "".

    """
    print("Успех. ", end="")
    if result:
        print(f"{result}")


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
