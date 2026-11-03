"""Модуль с константами проекта."""

import os

COLUMN_TYPES = {"str", "int", "bool"}

DATA_PATH = f"{os.path.dirname(__file__)}/../../data"
TABLES_METADATA_PATH = f"{DATA_PATH}/db_meta.json"
DEFAULT_METADATA_CONTENT = {"tables": {}}

DB_COMMANDS = {
    "create_table": (
        {
            ("create_table", "<имя_таблицы>", "<столбец1:тип> <столбец2:тип> ..."),
        },
        "создать таблицу.",
    ),
    "list_tables": (
        {
            ("list_tables",),
        },
        "показать список всех таблиц.",
    ),
    "drop_table": (
        {
            ("drop_table", "<имя_таблицы>"),
        },
        "удалить таблицу.",
    ),
    "insert": (
        {
            (
                "insert",
                "into",
                "<имя_таблицы>",
                "values",
                "(<значение1>, <значение2>, ...)",
            ),
        },
        "создать запись.",
    ),
    "select": (
        {
            (
                "select",
                "from",
                "<имя_таблицы>",
                "where",
                "<столбец> = <значение>",
            ),
            ("select", "from", "<имя_таблицы>"),
        },
        "прочитать записи из таблицы.",
    ),
    "update": (
        {
            (
                "update",
                "<имя_таблицы>",
                "set",
                "<столбец1> = <новое_значение1>",
                "where",
                "<столбец_условия> = <значение_условия>",
            ),
        },
        "обновить запись.",
    ),
    "delete": (
        {
            (
                "delete",
                "from",
                "<имя_таблицы>",
                "where",
                "<столбец> = <значение>",
            ),
        },
        "удалить запись.",
    ),
    "info": (
        {
            ("info", "<имя_таблицы>"),
        },
        "вывести информацию о таблице.",
    ),
}

GENERAL_COMMANDS = {
    "exit": ({("exit",)}, "выход из программы."),
    "help": ({("help",)}, "справочная информация."),
}

SPECIAL_SYMBOLS_IN_USER_ARGS = set("\"'()<>=.:")
SUPPORTED_COMPARSION_SYMBOLS = set("=")
