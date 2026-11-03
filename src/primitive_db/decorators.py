"""Декораторы для работы с функциями БД в engine.py."""

# Замечание по decorators.py - эти декораторы применены не к
# core.py, а к engine.py, потому что делать обёртки на ошибки
# в основной логике, чтобы они выводились на экран, а не просачивались
# дальше - опасно. Стоит какой-то непредвиденной ошибке выскочить
# и неграмотно составленное тестирование / тесировщик
# её просто не заметит, т.к. приложение продолжит работать,
# не падая с ошибкой. Любая непредвиденаня ошибка
# должна быть видна сразу и заметна всем.
# Именно поэтому декораторы применены к engine.py,
# точке входа cli, где вывод в терминал подразумевается по умолчанию
# и является единственной опцией.
#
# Errors should never pass silently.
# Unless explicitly silenced.
# - The Zen of Python.

from collections.abc import Callable, Iterable, Sequence
from functools import wraps
from json import JSONDecodeError
from typing import ParamSpec, TypeVar

from primitive_db.constants import SPECIAL_SYMBOLS_IN_USER_ARGS
from primitive_db.errors import (
    ColumnIsMissingError,
    TableAlreadyExistsError,
    TableIsMissingError,
)
from primitive_db.user_interaction import ask_confirmation, print_err

P = ParamSpec("P")
R = TypeVar("R")


# Дельта альфа бета штрих...
def check_user_input(
    user_input_formats: Iterable[Sequence[str]],
) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """Проверяет формат пользовательского ввода на соответствие формата команды.

    Проверяет ключевые слова, что состоят из букв и игнорирует слова, в которых
    есть спец символы <>()=

    Пример user_input_formats:
    - {
        ("select", "from", "<имя_таблицы>", "where", "<столбец> = <значение>"),
        ("select", "from", "<имя_таблицы>")
      }

    Args:
        user_input_formats (list): форматы пользовательского ввода

    """

    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        @wraps(func)
        def wrapper(
            command_args: list[str] | None = None,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R:
            user_input_is_correct = False
            for user_input_format in user_input_formats:
                user_input_is_correct = True

                for i in range(len(user_input_format)):
                    arg_format = user_input_format[i]
                    try:
                        arg = command_args[i]
                    except (IndexError, TypeError):
                        user_input_is_correct = False
                        break

                    # Если есть пересечение - игнорируем аргумент
                    if set(arg_format) & SPECIAL_SYMBOLS_IN_USER_ARGS:
                        continue

                    if arg.lower() != arg_format.lower():
                        user_input_is_correct = False
                        break

                # Если проходим хотя бы по одному формату - останавливаемся
                if user_input_is_correct:
                    break

            if user_input_is_correct:
                return func(*args, command_args=command_args, **kwargs)
            print_err("Пользовательский ввод имеет некорректный формат.")
            return None

        return wrapper

    return decorator


def handle_db_errors[**P, R](func: Callable[P, R]) -> Callable[P, R | None]:
    """Обрабатывает стандартные ошибки БД.

    Выводит на экран информацию об ошибках в зависимости от того,
    что вызовет функция.
    """

    def wrapper(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print_err(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована.",
            )
        except JSONDecodeError as e:
            print_err(f"Файлы БД повреждены. {e}")
        except TableAlreadyExistsError as e:
            print_err(f"Таблица уже существует. {e}")
        except TableIsMissingError as e:
            print_err(f"Таблицы не существует. {e}")
        except ColumnIsMissingError as e:
            print_err(f"Столбец не найден. {e}")
        except ValueError as e:
            print_err(f"Ошибка валидации: {e}")
        except Exception as e:
            print_err(f"Произошла непредвиденная ошибка: {e}")

    return wrapper


def confirm_action(
    action_name: str,
) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """Спрашивает у пользователя подтвержденние на действие."""

    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        @wraps(func)
        def wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R:

            if ask_confirmation("action_name"):
                return func(*args, **kwargs)
            return None

        return wrapper

    return decorator
