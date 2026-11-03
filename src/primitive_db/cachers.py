"""Содержит реализации методов кеширования."""

# Замечания:
# - К сожалению, реализовать через замыкания как просят по ТЗ валидно,
#   чтобы проходили тесты на изменения структуры (в случае пересоздания
#   таблицы через drop_table, create_table в пределах одной программы,
#   или даже простой update insert) не получилось. Вернее, это возможно,
#   но через global, что лишает использования замыканий вообще всех преимуществ
# - Так же как и реализовать абстрактное кеширование, не привязанное к
#   особенностям работы конкретной функции
# - Сам по себе механизм кеширования требует понимания контекста предметной
#   области и использование его в слепую (создание абстрактной функции
#   кеширования) - не только опасно, но и технически некорректно
# - Исходя из этих проблем было принято решение отойти от ТЗ с целью
#   получения заданных целевых характеристик (кеширование в пределах select)
# - Структура файлов задания так же была нарушена, т.к. оставлять её в том формате
#   в котором это было описано в ТЗ не имело смысла, файлы чётко выделялись на подблоки
#   что относились к изначальному описанию задачи крайне косвенног.

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from primitive_db.utils import CopyPolicy

P = ParamSpec("P")
R = TypeVar("R")


class TableCacher:
    """Класс, что кеширует вызов функции select таблицы."""

    def __init__(self) -> None:
        """Инициализирует объект."""
        self.cache = {}

    def create_cacher(self, func: Callable[P, R]) -> Callable[P, R | None]:
        """Декоратор. Кеширует select класса Table."""

        @wraps(func)
        def cache_result(
            _self: object,
            where_clause: dict | None = None,
            do_copy: CopyPolicy = CopyPolicy.DO_COPY,
        ) -> R:
            # Частная реализация хеширования специально для класса Table
            if where_clause is None:
                key = (_self.name,)
            else:
                key = (_self.name, tuple(where_clause.items()))

            if key in self.cache:
                return self.cache[key]
            result = func(_self, where_clause, do_copy)
            self.cache[key] = result
            return result

        return cache_result

    def clear_cache(self, table_name: str | None = None) -> None:
        """Очищает кеш.

        Еслт указан table_name, то очищает только указанную таблицу.

        Args:
            table_name (str, optional): название таблицы. По умолчанию None

        """
        if table_name is None:
            self.cache = {}
            return

        keys_to_delete = [key for key in self.cache if key[0] == table_name]

        for key in keys_to_delete:
            del self.cache[key]
