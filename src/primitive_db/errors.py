"""Содержит кастомные ошибки, связанные с работой БД."""


class TableAlreadyExistsError(ValueError):
    """Вызывается когда таблица уже существует с БД."""


class TableIsMissingError(KeyError):
    """Вызывается когда таблица отсутствует в БД."""


class ColumnIsMissingError(KeyError):
    """Вызывается когда колонка отсутствует в таблице."""


class CommandParseError(ValueError):
    """Вызывается когда парсинг команд вернул ошибку."""
