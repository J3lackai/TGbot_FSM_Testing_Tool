from cryptography.fernet import Fernet
from keyboard import wait
def beautiful_exit():
    print("Нажмите 'Enter' для завершения программы.")
    wait("enter")
    exit()
print("Ваш ключ:", end = "")
print(Fernet.generate_key().decode())
print("ВНИМАНИЕ: Не кому ни передавайте этот ключ! Если вы использовали ключ, тогда человек получивший доступ к ключу может украсть ваш Telegram аккаунт!")
print("Самостоятельно выполните установку ключа в переменные среды. Как это сделать подробно описано в файле ReadMe.")
beautiful_exit()