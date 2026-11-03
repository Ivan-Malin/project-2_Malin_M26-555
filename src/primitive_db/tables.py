"""Функции и классы по работе с таблицами БД."""

import json
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from primitive_db.cachers import TableCacher
from primitive_db.constants import COLUMN_TYPES, DATA_PATH
from primitive_db.errors import ColumnIsMissingError, TableIsMissingError
from primitive_db.utils import (
    CopyPolicy,
    OverwritePolicy,
    is_table_data_exist,
    is_table_exist,
    prepare_full_path,
    validate_value,
)


def is_columns_propper(columns: list[tuple[str, str]]) -> bool:
    """Проверяет является ли columns списком колонок таблицы.

    Args:
        columns (List[Tuple[str, str]]): колонки таблицы

    Returns:
        bool: является ли columns списком колонок таблицы.

    """
    # По хорошему это всё делать через классы, но т.з. есть т.з....
    if not isinstance(columns, Sequence):
        return False

    return all(
        isinstance(item, Sequence)
        and len(item) == len(("имя", type))
        and isinstance(item[0], str)
        and item[1] in COLUMN_TYPES
        for item in columns
    )


def does_columns_have_id(columns: list[tuple[str, str]]) -> bool:
    """Проверяет, имеет ли columns колонку с ID.

    Args:
        columns (List[Tuple[str, str]]): колонки таблицы

    Returns:
        bool: имеет ли хоть одна из колонок ID.

    """
    if not is_columns_propper(columns):
        msg = "columns должен быть списком колонок."
        raise TypeError(msg)

    return any(key == "ID" and key_type == "int" for (key, key_type) in columns)


def is_where_clause_propper(where_clause: dict[str, Any]) -> bool:
    """Проверяет, верная ли структура у where_clause."""
    if not isinstance(where_clause, dict):
        return False

    return all(isinstance(key, str) for key in where_clause)


class Table:
    """Класс для управления данными отдельной таблицы.

    Хранит метаданные (схему) и данные в памяти, а также предоставляет
    методы для сохранения и загрузки из JSON-файла.
    """

    cacher = TableCacher()

    def __init__(
        self,
        name: str,
        columns: list[tuple],
        data: list[dict] | None = None,
        do_copy: CopyPolicy = CopyPolicy.DO_NOT_COPY,
    ) -> None:
        """Инициализирует объект таблицы.

        Args:
            name (str): Название таблицы
            columns (list[tuple[str, str]]): упорядоченный список столбцов
                формата ("название", "тип_столбца"). тип_столбца один из
                COLUMN_TYPES. Столбец 'ID' добавляется автоматически,
                если его нет.
            data (list[dict]): Список словарей с данными.
                Если None, создается пустая таблица.
            do_copy (CopyPolicy): Копировать ли входные данные, или ссылаться на них.

        Raises:
            ValueError: Если схема некорректна.
            TypeError: Если типы данных в схеме неверны.

        """
        if not isinstance(name, str) or not name:
            msg = "Имя таблицы должно быть непустой строкой."
            raise ValueError(msg)

        if not isinstance(columns, list):
            msg = "Схема таблицы должна быть списком кортежей."
            raise TypeError(msg)

        if not does_columns_have_id(columns):
            msg = "columns не содержит поля ID"
            raise ValueError(msg)

        data_processed = data if data is not None else []

        self.copy = do_copy
        if do_copy == CopyPolicy.DO_COPY:
            self.columns = deepcopy(columns)
            self.name = deepcopy(name)
            self.data = deepcopy(data_processed)
        else:
            self.columns = columns
            self.name = name
            self.data = data_processed

        # Валидация существующих данных при инициализации
        for _record in self.data:
            self._validate_record_types(_record)
            self._validate_record_structure(_record)

    def _get_column_types(self) -> dict[str, str]:
        """Возвращает словарь {имя_столбца: тип}."""
        return {col[0]: col[1] for col in self.columns}

    def _validate_record_types(self, _record: dict) -> None:
        """Проверяет типы всех полей в записи согласно схеме."""
        col_types = self._get_column_types()
        for key, val in _record.items():
            if key in col_types:
                validate_value(val, col_types[key])

    def _validate_record_structure(self, _record: dict) -> None:
        """Проверяет наличие всех ключей из схемы."""
        expected_keys = {col[0] for col in self.columns}
        actual_keys = set(_record.keys())
        if actual_keys != expected_keys:
            missing = expected_keys - actual_keys
            extra = actual_keys - expected_keys
            msg = (
                f"Несоответствие структуры записи. "
                f"Отсутствуют: {missing}, Лишние: {extra}"
            )
            raise ValueError(msg)

    def _generate_id(self) -> int:
        """Генерирует новый ID на основе максимального существующего."""
        if not self.data:
            return 1
        max_id = max(_record.get("ID", 0) for _record in self.data)
        return max_id + 1

    def _is_where_passed(
        self,
        _record: list[Any],
        where_clause: dict[str, Any] | None = None,
    ) -> bool:
        """Проверяем, проходет ли _record по условию where."""
        _match = True
        for key, value in where_clause.items():
            if key not in _record or _record[key] != value:
                _match = False
                break
        return _match

    def insert(self, values: list[Any]) -> dict:
        """Добавляет новую запись в таблицу.

        Args:
            values (list[Any]): Список значений для столбцов (без ID).
                Количество должно соответствовать
                количеству столбцов минус 1 (ID).

        Returns:
            dict: Словарь созданной записи (ссылка на него в таблице).

        Raises:
            ValueError: Если количество значений не совпадает со схемой.
            TypeError: Если типы значений неверны.

        """
        # Исключаем ID из списка пользовательских столбцов для вставки
        user_columns = [col for col in self.columns if col[0] != "ID"]

        if len(values) != len(user_columns):
            msg = (
                f"Неверное количество значений. Ожидалось {len(user_columns)} "
                f"(для столбцов: {[c[0] for c in user_columns]}), "
                f"получено {len(values)}."
            )
            raise ValueError(msg)

        new_id = self._generate_id()
        new_record = {"ID": new_id}

        # Сопоставляем значения с именами столбцов
        for i, (col_name, col_type) in enumerate(user_columns):
            new_record[col_name] = validate_value(values[i], col_type)

        self.data.append(new_record)

        Table.cacher.clear_cache(self.name)

        return new_record

    # Декоратор применительно к методам класса применяется лишь раз
    # на объявлении класса, что спасает нас от несохранения кэша
    # при повторном load одной и той же таблицы из памяти в пределах
    # запуска одной программы
    @cacher.create_cacher
    def select(
        self,
        where_clause: dict[str, Any] | None = None,
        do_copy: CopyPolicy = CopyPolicy.DO_COPY,
    ) -> list[dict]:
        """Выбирает записи из таблицы.

        Args:
            where_clause: Словарь условий {column: value}.
                Если None, возвращает все записи.
            do_copy (CopyPolicy): Копировать ли входные данные, или ссылаться на них.

        Returns:
            list[dict]: Список подходящих записей.

        """
        if not where_clause:
            if do_copy == CopyPolicy.DO_COPY:
                return [deepcopy(_record) for _record in self.data]
            return self.data

        if not is_where_clause_propper(where_clause):
            msg = "where_clause некорректного формата."
            raise ValueError(msg)

        results = []
        for _record in self.data:
            if self._is_where_passed(_record, where_clause):
                if do_copy == CopyPolicy.DO_COPY:
                    results.append(deepcopy(_record))
                else:
                    results.append(_record)

        return results

    def update(self, set_clause: dict[str, Any], where_clause: dict[str, Any]) -> int:
        """Обновляет записи, удовлетворяющие условию.

        Args:
            set_clause: Словарь {column: new_value} для обновления.
            where_clause: Словарь условий для поиска записей.

        Returns:
            Количество обновленных записей.

        Raises:
            KeyError: Если столбец в set_clause не существует.
            TypeError: Если новое значение неверного типа.

        """
        col_types = self._get_column_types()
        updated_count = 0

        if not is_where_clause_propper(where_clause):
            msg = "where_clause некорректного формата."
            raise ValueError(msg)

        if not isinstance(set_clause, dict):
            msg = "set_clause должен быть словарём."
            raise TypeError(msg)

        # Проверяем существование столбцов в set_clause заранее
        set_clause_paresed = {}
        for col_name, new_value in set_clause.items():
            if col_name not in col_types:
                msg = f"Столбец '{col_name}' не существует в таблице '{self.name}'."
                raise ColumnIsMissingError(msg)
            if col_name == "ID":
                msg = "Изменение ID запрещено."
                raise ValueError(msg)
            set_clause_paresed[col_name] = validate_value(
                new_value,
                col_types[col_name],
            )

        for _record in self.data:
            if self._is_where_passed(_record, where_clause):
                # Применяем обновления
                for col_name, new_value in set_clause_paresed.items():
                    _record[col_name] = new_value
                updated_count += 1

        Table.cacher.clear_cache(self.name)

        return updated_count

    def delete(self, where_clause: dict[str, Any]) -> int:
        """Удаляет записи, удовлетворяющие условию.

        Args:
            where_clause: Словарь условий для поиска записей.

        Returns:
            Количество удаленных записей.

        """
        if not is_where_clause_propper(where_clause):
            msg = "where_clause некорректного формата."
            raise ValueError(msg)

        initial_len = len(self.data)
        # Оставляем только те записи, которые НЕ соответствуют условию
        self.data = [
            _record
            for _record in self.data
            if not all(_record.get(k) == v for k, v in where_clause.items())
        ]

        Table.cacher.clear_cache(self.name)

        return initial_len - len(self.data)

    @classmethod
    def copy(
        cls,
        table_data: "Table",
    ) -> "Table":
        """Копирует table_data.

        Args:
            table_data (Table): таблица для копирования

        Returns:
            Table: скопированная таблица

        """
        if not isinstance(table_data, cls):
            msg = f"Аргумент должен быть экземпляром класса {cls}."
            raise TypeError(msg)

        # Используем deepcopy для полной изоляции данных и структуры
        new_name = deepcopy(table_data.name)
        new_columns = deepcopy(table_data.columns)
        new_data = deepcopy(table_data.data)

        # Создаем новый экземпляр с скопированными данными
        # do_copy здесь не важен, так как мы уже передаем готовые копии,
        # но ставим DO_NOT_COPY для эффективности, чтобы конструктор
        # не копировал их снова.
        return cls(
            name=new_name,
            columns=new_columns,
            data=new_data,
            do_copy=table_data.copy,
        )

    @classmethod
    def load_table_by_metadata(
        cls,
        metadata: dict,
        table_name: str,
        data_path: str = DATA_PATH,
    ) -> "Table":
        """Зашружает таблицу на основе metadata.

        Args:
            metadata (dict): метаданные хранилища таблиц
            table_name (str): название таблицы
            data_path (str): путь до папки с данными БД.
                По умолчанию берёт папку data проекта primitive_db.

        Returns:
            Table: загруженная таблица

        """
        if not is_table_exist(
            metadata,
            table_name,
            data_path,
        ) or not is_table_data_exist(table_name, data_path):
            msg = f"Таблица {table_name} не существует в БД."
            raise TableIsMissingError(msg)

        columns = metadata["tables"][table_name]["columns"]
        table_path = metadata["tables"][table_name]["path"]
        return cls.load_table(table_path, table_name, columns)

    @classmethod
    def save_table_by_metadata(
        cls,
        metadata: dict,
        table: "Table",
        overwrite: OverwritePolicy = OverwritePolicy.DO_NOT_OVERWRITE,
        data_path: str = DATA_PATH,
    ) -> None:
        """Сохраняет таблицу на основе metadata.

        Args:
            metadata (dict): метаданные хранилища таблиц
            table (Table): исходная таблица
            overwrite (OverwritePolicy): перезаписывать ли таблицу,
                если она уже существует в БД.
            data_path (str): путь до папки с данными БД.
                По умолчанию берёт папку data проекта primitive_db.

        """
        table_name = table.name
        if not is_table_exist(metadata, table_name, data_path):
            msg = f"Таблица {table_name} не определена в metadata."
            raise TableIsMissingError(msg)

        if (
            is_table_data_exist(table_name, data_path)
            and overwrite == OverwritePolicy.DO_NOT_OVERWRITE
        ):
            msg = f"Таблица {table_name} уже существует в БД."
            raise TableIsMissingError(msg)

        table_path = metadata["tables"][table_name]["path"]
        cls.save_table(table, table_path)

    @classmethod
    def load_table(
        cls,
        file_path: str,
        table_name: str,
        columns: list[tuple[str, str]],
    ) -> "Table":
        """Загружает таблицу из JSON-файла.

        Формат файла:
        {
            "data": [...]
        }

        Args:
            file_path (str): Путь к JSON-файлу.
            table_name: Название таблицы.
            columns (List[Tuple[str, str]]): упорядоченный список столбцов
                формата ("название", "тип_столбца"). тип_столбца один из
                COLUMN_TYPES.

        Returns:
            Table: загруженная таблица

        Raises:
            FileNotFoundError: Если файл не найден.
            ValueError: Если структура файла неверна.

        """
        if not is_columns_propper(columns):
            msg = "columns должен быть списком колонок."
            raise TypeError(msg)

        if not isinstance(table_name, str):
            msg = "table_name должен быть str."
            raise TypeError(msg)

        # Ошибки файла и json пробрасываем дальше
        with open(file_path, encoding="utf-8") as f:
            content = json.load(f)

        data = content.get("data", [])

        return cls(name=table_name, columns=columns, data=data)

    @classmethod
    def save_table(cls, table: "Table", file_path: str | Path) -> None:
        """Сохраняет состояние таблицы в JSON-файл.

        Args:
            table: Экземпляр таблицы для сохранения.
            file_path: Путь для сохранения.

        """
        # Создаем директорию, если её нет
        prepare_full_path(file_path)

        # Не смотря на возможности формата json, не храним в самой таблице
        # метаданные для масштабируемости и совместимости с другими форматами
        # в будущем (за счёт хранения метаданных в metadata файле)
        serializable_data = {
            "data": table.data,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def clear_cache(table_name: str | None = None) -> None:
        """Очищает кэш вызова select.

        Если не указана таблица, то очищает весь кэш.

        Args:
            table_name (str | None, optional): название таблицы.
                По умолчанию None.

        Raises:
            TypeError: при несоответствии аргументов

        """
        if table_name is None:
            Table.cacher.clear_cache()
        else:
            if not isinstance(table_name, str):
                msg = "table_name должен быть str"
                raise TypeError(msg)

            Table.cacher.clear_cache(table_name)

    def __hash__(self) -> int:
        """Хеширует класс на основе имени и данных о колонках."""
        return hash((self.name, self.columns))

    def __eq__(self, other: "Table") -> bool:
        """Сравнивает класс на основе имени и данных о колонках."""
        if not isinstance(other, Table):
            msg = (
                f'Некорректно сравнивать "{type(self).__name__}"'
                f'с классом "{type(other).__name__}".'
            )
            raise TypeError(msg)

        return (self.name, self.columns) == (other.name, other.columns)

    def __repr__(self) -> str:
        """Возвращает краткое представление класса Table.

        Returns:
            str: краткое представление.

        """
        return f"Table(name='{self.name}', records_count={len(self.data)})"
