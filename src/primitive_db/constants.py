"""Модуль с константами проекта."""

from primitive_db.utils import get_current_path

COLUMN_TYPES = ("str", "int", "bool")
TABLES_METADATA_PATH = f"{get_current_path()}/db_meta.json"
