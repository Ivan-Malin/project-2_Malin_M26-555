"""Модуль для парсинга SQL-подобных команд пользователя."""

from typing import Any


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
