from primitive_db.parser import (
    parse_insert_values,
    parse_where_clause,
    tokenize_user_args,
)

# --- Тесты для tokenize_user_args ---


def test_tokenize_basic_command():
    """Базовый тест: простая команда без спецсимволов."""
    args = ["create_table", "users", "name:str", "age:int"]
    result = tokenize_user_args(args)
    assert result == ["create_table", "users", "name:str age:int"]


def test_tokenize_insert_with_simple_values():
    """Тест вставки с простыми значениями в скобках."""
    args = ["insert", "into", "t", "values", "(1,", "2,", "3)"]
    result = tokenize_user_args(args)
    # Скобки должны остаться, так как их удаляет parse_insert_values,
    # но они должны быть собраны в один токен
    assert len(result) == 5
    assert result[4] == "(1, 2, 3)"


def test_tokenize_string_with_spaces_and_commas():
    """Критический тест: строка с пробелами и запятыми внутри кавычек."""
    # Имитация ввода: insert into t values ("Hello, World", 123)
    # shlex мог разбить это на: ['"Hello,', 'World",', '123)']
    args = ["insert", "into", "t", "values", '"Hello,', 'World",', "123)"]
    result = tokenize_user_args(args)

    # Лексер должен собрать всё внутри кавычек и скобок корректно
    # Ожидаем, что аргумент values будет одним блоком или двумя, но склеенными
    # В текущей реализации: tokens.append(current_token) при пробеле вне скобок/кавычек.
    # Но внутри кавычек пробел игнорируется.
    # Проверим, что "Hello, World" не разорвалось.
    assert any("Hello, World" in t for t in result)
    assert any("123" in t for t in result)


def test_tokenize_nested_parentheses_in_string():
    """Тест: скобки внутри строки (не должны считаться управляющими)."""
    # Ввод: values ("func()", 1)
    args = ["values", '("func()",', "1)"]
    result = tokenize_user_args(args)

    # "(" внутри кавычек не должна увеличивать paren_depth
    found_token = next((t for t in result if "func()" in t), None)
    assert found_token is not None
    assert "(" in found_token and ")" in found_token


def test_tokenize_complex_injection_attempt():
    """Тест из ТЗ: сложная строка с кириллицей, двоеточиями и запятыми."""
    # Ввод: values ("Alice ,Nigger:Айлюлю.,", 5000)
    args = ["values", '("Alice', ',Nigger:Айлюлю.,",', "5000)"]
    result = tokenize_user_args(args)

    # Должен собраться один токен для аргументов values
    values_arg = result[-1]
    assert "Alice ,Nigger:Айлюлю.," in values_arg
    assert "5000" in values_arg


def test_tokenize_where_clause_with_spaces():
    """Тест: условие where с пробелами вокруг знака равенства."""
    args = ["select", "from", "t", "where", "name", "=", '"Admin"']
    result = tokenize_user_args(args)

    # Должно склеиться в "name = "Admin""
    where_part = next((t for t in result if "name" in t), None)
    assert where_part is not None
    assert "=" in where_part
    assert '"Admin"' in where_part


def test_tokenize_mixed_quotes():
    """Тест: использование разных типов кавычек (если поддерживается)."""
    args = ["values", "'single'", '"double"']
    result = tokenize_user_args(args)

    # Проверяем, что кавычки сохранились для дальнейшего парсинга
    assert any("'single'" in t for t in result)
    assert any('"double"' in t for t in result)


def test_tokenize_empty_parentheses():
    """Тест: пустые скобки."""
    args = ["values", "()"]
    result = tokenize_user_args(args)
    assert result == ["values", "()"]


def test_tokenize_unbalanced_parentheses():
    """Тест: незакрытая скобка (должна обработаться gracefully)."""
    args = ["values", "(1,", "2"]
    result = tokenize_user_args(args)
    # Лексер просто соберет всё в токен, так как paren_depth не обнулится
    assert any("(1, 2" in t for t in result)


# --- Тесты для parse_insert_values ---


def test_parse_values_basic_types():
    """Тест: парсинг int, str, bool."""
    input_str = '(1, "hello", true, false)'
    result = parse_insert_values(input_str)
    assert result == [1, "hello", True, False]


def test_parse_values_string_with_commas():
    """Тест: строка, содержащая запятые (главная фича)."""
    input_str = '("a,b,c", 1)'
    result = parse_insert_values(input_str)
    assert result == ["a,b,c", 1]


def test_parse_values_string_with_parentheses():
    """Тест: строка, содержащая скобки."""
    input_str = '("func(x)", 2)'
    result = parse_insert_values(input_str)
    assert result == ["func(x)", 2]


def test_parse_values_complex_injection_parsed():
    """Тест: полный разбор сложной строки из теста токенизации."""
    # После токенизации мы получаем строку вида: "Alice ,Nigger:Айлюлю.,", 5000
    # Или даже со скобками, если они не были удалены: ("Alice ,Nigger:Айлюлю.,", 5000)
    input_str = '("Alice ,Nigger:Айлюлю.,", 5000)'
    result = parse_insert_values(input_str)

    assert len(result) == 2
    assert result[0] == "Alice ,Nigger:Айлюлю.,"
    assert result[1] == 5000


def test_parse_values_empty_string_inside_quotes():
    """Тест: пустая строка в кавычках."""
    input_str = '("", 1)'
    result = parse_insert_values(input_str)
    assert result == ["", 1]


def test_parse_values_no_brackets():
    """Тест: входная строка уже без скобок (после токенизации)."""
    input_str = '"test", 123'
    result = parse_insert_values(input_str)
    assert result == ["test", 123]


# --- Интеграционный тест парсера условий ---


def test_parse_where_with_quoted_value():
    """Тест: парсинг условия where со строковым значением."""
    condition_str = 'name = "Ivan Ivanov"'
    result = parse_where_clause(condition_str)
    assert result == {"name": "Ivan Ivanov"}
