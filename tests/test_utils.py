import json
from pathlib import Path

from primitive_db.utils import load_metadata, save_metadata


def test_load_metadata_success(tmp_path: Path) -> None:
    simple_json_content = {
        "id": 1024,
        "username": "ivan_dev",
        "is_active": True,
        "skills": ["Python", "Django", "Docker"],
        "profile": {
            "first_name": "Иван",
            "last_name": "Петров",
            "email": "ivan@example.com",
        },
        "experience_years": 3.5,
        "metadata": None,
    }

    # Сами же файл и создаём
    simple_json_path = tmp_path / "simple_json.json"
    simple_json_path.write_text(
        json.dumps(simple_json_content, ensure_ascii=False), encoding="utf-8"
    )

    # Проверяем его парсинг
    assert load_metadata(simple_json_path) == simple_json_content


def test_load_metadata_bad_data(tmp_path: Path) -> None:
    # Парсинг папки должен выдавать ошибку, т.к. мы этот случай не обрабатываем

    is_a_directory_error_catched = False
    try:
        load_metadata(tmp_path)
    except IsADirectoryError:
        is_a_directory_error_catched = True

    assert is_a_directory_error_catched, (
        "load_metadata не умеет выбрасывать IsADirectoryError"
    )

    # Парсинг отсутствующего файла
    assert load_metadata(tmp_path / "DOSTOYEVSKY_PRESTUPLENIYE_I_NAKAZANIYE.json") == {}


def test_save_metadata(tmp_path: Path):
    simple_json_content = {
        "id": 1024,
        "username": "ivan_dev",
        "is_active": True,
        "skills": ["Python", "Django", "Docker"],
        "profile": {
            "first_name": "Иван",
            "last_name": "Петров",
            "email": "ivan@example.com",
        },
        "experience_years": 3.5,
        "metadata": None,
    }

    # Сами же файл и создаём
    simple_json_path = tmp_path / "simple_json.json"
    save_metadata(simple_json_path, simple_json_content)

    # Проверяем его парсинг
    assert load_metadata(simple_json_path) == simple_json_content


def test_save_metadata_bad_values(tmp_path: Path):

    # Сами же файл и создаём
    simple_json_path = tmp_path / "simple_json.json"

    wrong_data_catched_fl = False
    try:
        save_metadata(simple_json_path, "WTF")
    except TypeError:
        wrong_data_catched_fl = True
    assert wrong_data_catched_fl, (
        "save_metadata не умеет выбрасывать исключения аргумента"
    )

    is_a_directory_error_catched = False
    try:
        load_metadata(tmp_path)
    except IsADirectoryError:
        is_a_directory_error_catched = True

    assert is_a_directory_error_catched, (
        "save_metadata не умеет выбрасывать IsADirectoryError"
    )
