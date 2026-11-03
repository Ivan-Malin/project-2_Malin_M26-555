"""Содержит функции по выводы информации."""

from prettytable import PrettyTable

from primitive_db.constants import DB_COMMANDS, GENERAL_COMMANDS
from primitive_db.tables import Table


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
