"""Декораторы для работы с функциями БД в engine.py."""

from collections.abc import Callable, Iterable, Sequence
from functools import wraps
from typing import ParamSpec, TypeVar

from primitive_db.constants import SPECIAL_SYMBOLS_IN_USER_ARGS
from primitive_db.printing import print_err

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

    return decorator  # возвращаем декоратор
