import os
from loguru import logger
import asyncio
import sys
from telethon import TelegramClient
from pathlib import Path
from telethon.sessions import StringSession
from cryptography.fernet import Fernet
from coroutines import communicating_with_bot, check_bot_availability
from dotenv import load_dotenv
from load_data import get_data_from_conf, get_data_from_env

def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data).decode()
    return decrypted_data

def testing_bots() ->tuple[list[bool], tuple[str], str]:
    # Загружаем переменные из файла .env
    dotenv_path = Path('.') / '.env'
    load_dotenv(dotenv_path=dotenv_path)

    # Достаём данные из переменных окружения
    api_id, api_hash, phone, encryption_key, encrypted_session = get_data_from_env()

    # Достаём данные из конфига
    wait, lvl_log, tuple_tests, list_res, tuple_bots,  test_flag, dc = get_data_from_conf()
    logger.remove()
    logger.add(sys.stderr, format = "|<green> {time: HH:mm:ss} </green>| <level> {level} </level> | {message}", level = lvl_log)
    logger.add(os.path.join("result.log"),
               format="|{time:YYYY.MM.DD HH:mm}|{level}|{message}|", level="DEBUG", rotation="500 kb")

    logger.info("Список ботов:")
    for i in range(1, len(tuple_bots) + 1):
        logger.info(f"{tuple_bots[i - 1]} ({i})")

    count = int(
        input('Введите: номер бота которого нужно тестировать. (Начиная от единицы): '))
    if not (0 <= count <= len(tuple_bots)):
        logger.critical("Ошибка: Неправильный номер бота.")
        raise

    bot_username_tg = tuple_bots[count - 1]
    logger.info("Выбрали бота...")
    # Оборачиваем асинхронный код в функцию для запуска asyncio.run

    async def run_test(phone, encryption_key) -> list[bool] | None:
        # Проверяем наличие ключа шифрования. Если нет, то создаем и сохраняем.
        try:
            session = StringSession()
            if encrypted_session:
                session_str = decrypt_data(
                    encrypted_session.encode(), encryption_key)
                session = StringSession(session_str)
            if test_flag:
                client = TelegramClient(session, api_id, api_hash)
                client.session.set_dc(dc, '149.154.167.40', 80)
            else:
                client = TelegramClient(session, api_id, api_hash)
            
            await client.start(phone=phone)  # Запуск процесса авторизации
            # Проверка доступности бота
            if not encrypted_session and session.auth_key: # Если сессии не было и мы авторизовались
                session_str = session.save()
                f = Fernet(encryption_key.encode()) # Ключ должен быть bytes
                encrypted_session_bytes = f.encrypt(session_str.encode())
                new_encrypted_session = encrypted_session_bytes.decode()
                # Записываем ENCRYPTED_SESSION в файл .env
                try:
                    # Читаем текущий .env, чтобы не потерять другие переменные
                    env_lines = []
                    if dotenv_path.exists():
                        with open(dotenv_path, "r") as f:
                            env_lines = f.readlines()
                    
                    # Удаляем старую строку ENCRYPTED_SESSION, если она есть
                    env_lines = [line for line in env_lines if not line.strip().startswith("ENCRYPTED_SESSION=")]
                    
                    # Добавляем новую строку
                    env_lines.append(f"ENCRYPTED_SESSION={new_encrypted_session}\n")
                    
                    # Перезаписываем файл .env
                    with open(dotenv_path, "w") as f:
                        f.writelines(env_lines)
                    logger.info("Новая зашифрованная сессия сохранена в .env")
                    # Обновляем переменную для текущего выполнения (если нужно)
                    # encrypted_session = new_encrypted_session
                except Exception as e_write:
                    logger.error(f"Не удалось записать зашифрованную сессию в .env: {e_write}")
            if not await check_bot_availability(client, bot_username_tg):
                logger.critical("Бот недоступен.")
                choice = input(
                    "Введите 1 чтобы повторно проверить готовность бота, 0 чтобы выйти: ")
                if choice == '1':
                    if not await check_bot_availability(client, bot_username_tg):
                        logger.warning("Бот так и не ответил.  Завершаем.")
                        await client.disconnect()
                        return None # Выходим, если бот по-прежнему недоступен
                else:
                    logger.info("Завершаем тестирование.")
                    await client.disconnect()
                    return None # Завершаем если пользователь хочет выйти

            """Получает информацию о пользователе, боте, чате или канале по его имени пользователя. Возвращает объект telethon.types.User"""
            bot_entity = await client.get_entity(bot_username_tg)

            for i in range(len(tuple_tests)):
                # Передаем client и bot_entity
                list_res[i] = await communicating_with_bot(client, bot_entity, tuple_tests[i], timeout=wait)
                if list_res[i] < 0:
                    logger.error(f"Ошибка проведения теста {tuple_tests[i]}!")
                    await client.disconnect()  # Закрываем соединение
                    None
                else:
                    list_res[i] = bool(list_res[i])
            await client.disconnect()
            return list_res
        except Exception as e:
            logger.exception(f"Произошла ошибка во время тестирования: {e}")

    try:
        list_res = asyncio.run(run_test(phone, encryption_key))
        return list_res, tuple_tests, bot_username_tg
    except Exception:
        raise