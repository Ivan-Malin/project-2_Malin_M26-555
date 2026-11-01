"""Модуль с константами проекта."""

import os

COLUMN_TYPES = {"str", "int", "bool"}

DATA_PATH = f"{os.path.dirname(__file__)}/../../data"
TABLES_METADATA_PATH = f"{DATA_PATH}/db_meta.json"
DEFAULT_METADATA_CONTENT = {"tables": {}}

HELP_TEXT = """
***Процесс работы с таблицей***
Функции:
<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу
<command> list_tables - показать список всех таблиц
<command> drop_table <имя_таблицы> - удалить таблицу
<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...)\
 - создать запись.
<command> select from <имя_таблицы> where <столбец> = <значение>\
 - прочитать записи по условию.
<command> select from <имя_таблицы> - прочитать все записи.
<command> update <имя_таблицы> set <столбец1> = <новое_значение1>\
 where <столбец_условия> = <значение_условия> - обновить запись.
<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить запись.
<command> info <имя_таблицы> - вывести информацию о таблице.

Общие команды:
<command> exit - выход из программы
<command> help - справочная информация
"""
