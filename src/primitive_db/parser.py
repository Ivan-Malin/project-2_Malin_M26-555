"""Модуль для парсинга SQL-подобных команд пользователя."""

from typing import Any

from primitive_db.constants import COLUMN_TYPES, SUPPORTED_COMPARSION_SYMBOLS
from primitive_db.errors import CommandParseError


# Пункт про arg1:type1 arg2:type2 напрямую исходит
# из ТЗ, в котором create_table
# имеет синтаксис без запятых...
# Стоит отметить, что тут охвачены не 100% случаев,
# но как минимум те, что предписаны help функцией
# охвачены полностью
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
    - Всё что в кавычках
    - Всё что не в кавычках и в скобках

    Args:
        args (list[str]): список токенов после shlex.split

    Returns:
        list[str]: обработанный список токенов

    """
    # Собираем всё обратно в одну строку, текущий обработчик
    # более умный, но т.к. менять старый код - что-то опять ломать,
    # то было принято решение оставить args как лист для совместимости
    #
    # Т.е. используется подход с посимвольной обработкой (lexer)
    full_line = " ".join(args)

    tokens = []
    current_token = ""
    i = 0
    n = len(full_line)

    in_quotes = False
    quote_char = None
    paren_depth = 0

    # 1. Склеиваем по признаку кавычек и скобок
    while i < n:
        char = full_line[i]

        # 1. Логика кавычек (высший приоритет)
        if char in ('"', "'"):
            if not in_quotes:
                in_quotes = True
                quote_char = char
                # Мы сохраняем кавычку в токене, чтобы parse_insert_values
                # мог сам её обработать или удалить.
                current_token += char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
                current_token += char
            else:
                # Другая кавычка внутри текущей (например ' внутри ")
                current_token += char
            i += 1
            continue

        # Если мы внутри кавычек, берем всё подряд (скобки, пробелы, запятые)
        if in_quotes:
            current_token += char
            i += 1
            continue

        # 2. Логика скобок (только если не в кавычках)
        if char == "(":
            paren_depth += 1
            current_token += char
            i += 1
            continue

        if char == ")" and paren_depth > 0:
            paren_depth -= 1
            current_token += char
            i += 1
            continue
            # Если закрывающая скобка без открывающей — просто добавляем как символ

        # 3. Логика разделителей (разделителем считается только пробел)
        if char == (" ") and paren_depth == 0:
            if current_token:
                tokens.append(current_token)
                current_token = ""
            i += 1
            continue

        # 4. Все остальные символы
        current_token += char
        i += 1

    # Добавляем последний токен, если он есть
    if current_token:
        tokens.append(current_token)

    # 2. Склеиваем по признаку arg:val и arg = val
    final_tokens = []
    j = 0
    m = len(tokens)

    while j < m:
        token = tokens[j]

        # Склейка условий: arg = val (если знак равенства был разбит пробелом)
        if j + 2 < m and tokens[j + 1] in SUPPORTED_COMPARSION_SYMBOLS:
            combined = f"{token} {tokens[j + 1]} {tokens[j + 2]}"
            final_tokens.append(combined)
            j += 3
            continue

        # Склейка типов для create_table (arg:type arg:type)
        if final_tokens:
            last = final_tokens[-1]
            # Если предыдущий токен заканчивается на запятую
            # Или если оба токена содержат двоеточие
            if ":" in last and ":" in token and "=" not in token:
                final_tokens[-1] = f"{last} {token}"
                j += 1
                continue

        final_tokens.append(token)
        j += 1

    return final_tokens


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
        raise CommandParseError(msg)

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
        CommandParseError: Если формат строки неверен.

    """
    if not condition_str or "=" not in condition_str:
        return {}

    # Разделяем по первому знаку '=', чтобы поддержать значения, содержащие '='
    parts = condition_str.split("=")
    if len(parts) != len(("имя", type)):
        msg = f"Неверный формат условия: '{condition_str}'"
        raise CommandParseError(msg)

    key = parts[0].strip()
    value_str = parts[1].strip()

    if not key:
        msg = f"Отсутствует имя столбца в условии: '{condition_str}'"
        raise CommandParseError(msg)

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

    if not values:
        msg = "Отсутствуют элементы внутри скобок."
        raise CommandParseError(msg)

    return values


def _convert_value(val_str: str) -> Any:
    """Преобразует строковое представление значения в соответствующий тип Python.

    Правила:
    - "true"/"false" (регистронезависимо) -> bool
    - Цифры -> int
    - Значения в кавычках (уже очищенные от них) -> str
    - Остальное -> str
    """
    if val_str.lower() == "true":
        return True
    if val_str.lower() == "false":
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
    # Удаляем внешние кавычки, если они есть
    if (
        len(val_str) >= len('""')
        and val_str[0] == val_str[-1]
        and val_str[0] in ('"', "'")
    ):
        val_str = val_str[1:-1]

    return val_str
