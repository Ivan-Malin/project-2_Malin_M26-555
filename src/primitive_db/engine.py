import prompt

# По прицнпу YAGNI, пока нифига не известно ТЗ, делаем самым примитивным образом
WELCOME_STRING = """***
 <command> exit - выйти из программы
 <command> help - справочная информация"""

def welcome():
    print(WELCOME_STRING)
    user_input = prompt.string("Введите команду: ")
    return user_input