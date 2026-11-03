"""Модуль для парсинга SQL-подобных команд пользователя."""

from typing import Any

from primitive_db.constants import COLUMN_TYPES, SUPPORTED_COMPARSION_SYMBOLS


# Пункт про arg1:type1 arg2:type2 напрямую исходит
# из корявого ТЗ, в котором create_table
# имеет синтаксис без запятых...
def tokenize_user_args(args: list[str]) -> list[str]:
    """Токенизирует аргументы.

    Объединяет элементы списка по правилам:
    - Убирает скобки
    - Выражения вида arg = val в один элемент
    - Несколько подряд идущих элементов через запятую
      a, b, c, d = e
      в один элемент
    - Так же объединяет в 1 элемент элементы формата
      arg1:type1 arg2:type2.

    Args:
        args (list[str]): список токенов после shlex.split

    Returns:
        list[str]: обработанный список токенов

    """
    tokens = []
    i = 0

    while i < len(args):
        arg = args[i]
        arg = arg.replace("(", "").replace(")", "")
        token = ""

        # Обработка выражений с '=': если текущий токен не содержит '=',
        # но следующий токен это '='
        if i + 2 < len(args) and args[i + 1] in SUPPORTED_COMPARSION_SYMBOLS:
            # Объединяем arg = val в один элемент
            combined = f"{args[i]} {args[i + 1]} {args[i + 2]}"
            token = combined
            i += 3

        # Обычный случай - просто добавляем токен
        else:
            token = arg
            i += 1

        # Если предыдущий токен заканчился на ",",
        # значит мы лишь его часть
        if (tokens and tokens[-1].endswith(",")) or (
            tokens and (":" in tokens[-1]) and (":" in token)
        ):
            tokens[-1] += f" {token}"
        else:
            tokens.append(token)

    return tokens


def parse_column_str(column_str: str) -> tuple[str, str]:
    """Возвращает колонку из её строкового представления.

    Args:
        column_str (str): строковое представление колонки.

    Returns:
        tuple[str, str]: колонка

    """
    column_name, column_type = column_str.split(":")
    if column_type not in COLUMN_TYPES:
        msg = f"Неправильный тип колонки: {column_type}, не один из {COLUMN_TYPES}"
        raise TypeError(
            msg,
        )

    return (column_name, column_type)


def parse_condition(condition_str: str) -> dict[str, Any]:
    r"""Парсит строку условия (where_clause или set_clause) в словарь.

    Поддерживает форматы:
    - "column = value"
    - "column=value"

    Args:
        condition_str (str): Строка вида "age = 28" или "name = \"Sergei\"".

    Returns:
        dict[str, Any]: Словарь для присвоения / поиска записей.

    Raises:
        ValueError: Если формат строки неверен.

    """
    if not condition_str or "=" not in condition_str:
        return {}

    # Разделяем по первому знаку '=', чтобы поддержать значения, содержащие '='
    parts = condition_str.split("=")
    if len(parts) != len(("имя", type)):
        msg = f"Неверный формат условия: '{condition_str}'"
        raise ValueError(msg)

    key = parts[0].strip()
    value_str = parts[1].strip()

    if not key:
        msg = f"Отсутствует имя столбца в условии: '{condition_str}'"
        raise ValueError(msg)

    value = _convert_value(value_str)
    return {key: value}


def parse_where_clause(where_str: str) -> dict[str, Any]:
    """Парсит полную секцию where. Поддерживает только равенство.

    Args:
        where_str (str): Строка после ключевого слова where.

    Returns:
        dict[str, Any]: Словарь условий для поиска записей.

    """
    return parse_condition(where_str)


def parse_set_clause(set_str: str) -> dict[str, Any]:
    """Парсит секцию set.

    В простой реализации поддерживается обновление одного поля.
    Пример: "age = 29" -> {"age": 29}

    Args:
        set_str (str): Строка после ключевого слова set.

    Returns:
        dict[str, Any]: Словарь выражений для присвоения записей.

    """
    return parse_condition(set_str)


def parse_insert_values(values_str: str) -> list[Any]:
    """Парсит список значений из команды insert.

    Ожидает строку внутри скобок: "(val1, val2, ...)"

    Args:
        values_str: Строка со значениями, например: '"Sergei", 28, true'

    Returns:
        Список приведенных значений.

    """
    # Убираем внешние скобки, если они есть
    clean_str = values_str.strip()
    if clean_str.startswith("(") and clean_str.endswith(")"):
        clean_str = clean_str[1:-1]

    if not clean_str:
        return []

    values = []
    # Простой парсер, учитывающий кавычки
    current_val = ""
    in_quotes = False
    quote_char = None

    for char in clean_str:
        if char in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = char
            continue  # Не добавляем саму кавычку в значение
        if char == quote_char and in_quotes:
            in_quotes = False
            quote_char = None
            continue
        if char == "," and not in_quotes:
            values.append(_convert_value(current_val.strip()))
            current_val = ""
            continue

        current_val += char

    # Добавляем последнее значение
    if current_val.strip():
        values.append(_convert_value(current_val.strip()))

    return values


def _convert_value(val_str: str) -> Any:
    """Преобразует строковое представление значения в соответствующий тип Python.

    Правила:
    - "true"/"false" (регистронезависимо) -> bool
    - Цифры -> int
    - Значения в кавычках (уже очищенные от них) -> str
    - Остальное -> str
    """
    val_lower = val_str.lower()

    if val_lower == "true":
        return True
    if val_lower == "false":
        return False

    try:
        return int(val_str)
    except ValueError:
        pass

    try:
        return float(val_str)
    except ValueError:
        pass

    # Если значение было в кавычках, оно уже пришло сюда без них.
    # Если нет, то считаем его строкой.
    return val_str
