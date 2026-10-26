"""Содержит запуск, игровой цикл и парсинг команд."""

import prompt

# По прицнпу YAGNI, пока нифига не известно ТЗ, делаем самым примитивным образом
WELCOME_STRING = """***
 <command> exit - выйти из программы
 <command> help - справочная информация"""


def welcome() -> str:
    """Welcome-функция, получающая ввод пользователя.

    Returns:
        str: название команды

    """
    print(WELCOME_STRING)
    return prompt.string("Введите команду: ")
