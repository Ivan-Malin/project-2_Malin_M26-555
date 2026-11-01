"""Содержит кастомные ошибки, связанные с работой таблиц."""


class TableAlreadyExistsError(ValueError):
    """Вызывается когда таблица уже существует с БД."""


class TableIsMissingError(ValueError):
    """Вызывается когда таблица отсутствует в БД."""
