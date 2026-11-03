from unittest.mock import patch

from primitive_db.decorators import check_user_input

# Замечание проверяющему - часть тестовых файлов были отданы на откуп Qwen'у,
# т.к. тесты от нейросети (под пристальным ревью) лучше, чем никаких тестов вообще.
# Да и в ТЗ не оговорено, что вообще тесты нужны


# Тестовая функция-заглушка
def dummy_func(*args, **kwargs):
    return "Success"


# Определяем форматы команд для тестирования декоратора
TEST_FORMATS = [
    ("select", "from", "<имя_таблицы>", "where", "<столбец> = <значение>"),
    ("select", "from", "<имя_таблицы>"),
    ("create_table", "<имя_таблицы>", "<столбец1:тип>"),
]

# Создаем декорированную функцию один раз для всех тестов
decorated_dummy = check_user_input(TEST_FORMATS)(dummy_func)


@patch("primitive_db.decorators.print_err")
def test_valid_simple_command(mock_print_err):
    """Тест успешного выполнения простой команды."""
    command_args = ["select", "from", "users"]
    result = decorated_dummy(command_args)

    assert result == "Success", f"Ожидался 'Success', получено {result}"
    mock_print_err.assert_not_called()


@patch("primitive_db.decorators.print_err")
def test_valid_complex_command(mock_print_err):
    """Тест успешного выполнения команды с условием where."""
    command_args = ["select", "from", "users", "where", "id = 1"]
    result = decorated_dummy(command_args)

    assert result == "Success"
    mock_print_err.assert_not_called()


@patch("primitive_db.decorators.print_err")
def test_invalid_command_word(mock_print_err):
    """Тест ошибки при опечатке в ключевом слове."""
    command_args = ["selct", "from", "users"]
    result = decorated_dummy(command_args)

    assert result is None
    mock_print_err.assert_called_once()


@patch("primitive_db.decorators.print_err")
def test_invalid_input_type(mock_print_err):
    """Тест ошибки, если ввод не является списком/кортежем."""
    command_args = "not a list"
    result = decorated_dummy(command_args)

    assert result is None
    mock_print_err.assert_called_once()


@patch("primitive_db.decorators.print_err")
def test_case_insensitivity(mock_print_err):
    """Тест регистронезависимости (SELECT vs select)."""
    command_args = ["SELECT", "FROM", "Users"]
    result = decorated_dummy(command_args)

    assert result == "Success"
    mock_print_err.assert_not_called()


@patch("primitive_db.decorators.print_err")
def test_wrong_length(mock_print_err):
    """Тест ошибки при неверной длине аргументов."""
    command_args = ["select", "from"]  # Слишком коротко
    result = decorated_dummy(command_args)

    assert result is None
    mock_print_err.assert_called_once()
