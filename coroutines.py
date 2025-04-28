import time
import asyncio
from loguru import logger
import telethon
import random

async def check_bot_availability(client: telethon.TelegramClient, bot_username: str, timeout: int = 10):
    """Проверяет доступность бота, отправляя ему сообщение и ожидая ответа."""
    try:

        """await оператор который управляет потоком выполнения асинхронных операций. Работает с awaitable объектами"""

        bot_entity = await client.get_entity(bot_username)
        # Уникальное тестовое сообщение!
        test_message = "test_ping_" + str(time.time())
        await client.send_message(bot_entity, test_message)

        start_time = time.time()
        while time.time() - start_time < timeout:

            """get_messages возвращает список объектов telethon.types.Message, в нашем случае с одним объектом.
                Объект из себя представляет сообщение из чата."""
            
            messages = await client.get_messages(bot_entity, limit=1)
            if messages:
                last_message = messages[0] # Объект telethon.types.Message
                # Проверяем, что сообщение пришло от бота и отличается от нашего запроса
                if last_message.sender_id == bot_entity.id and last_message.message != test_message:
                    logger.info(f"Бот {bot_username} доступен.")
                    return True
            await asyncio.sleep(random.uniform(1.2, 2.2))

        logger.warning(
            f"Бот {bot_username} не ответил в течение {timeout} секунд.")
        return False

    except Exception as e:
        logger.error(f"Ошибка при проверке доступности бота: {e}")
        return False


async def communicating_with_bot(client, bot_entity: telethon.types.User, file_for_testing, timeout=10) -> int:
    """
    Взаимодействие с ботом, получение ответов через Telethon API.
    """
    try:
        file = open(file_for_testing, 'r')
        line = file.readline()
        while line != '':
            
            if line == '\n':
                line = file.readline()
                continue

            """Парсим файл с тестами, с каждой не пустой строки файла 
            достаём команду которую нужно отправить и ответ от бота (реакцию) которую ожидаем получить"""

            line = line.replace("\n", '')
            command_expected_answer = line.split('\\')
            command = command_expected_answer[0]
            expected_answer = command_expected_answer[1] if len(
                command_expected_answer) > 1 else None

            logger.info(
                f"Отправляем боту команду: {command}, Ожидаем ответ: {expected_answer}")

            # Отправляем команду боту через Telethon API
            await client.send_message(bot_entity, command)

            """Отправление сообщение боту. entity: Получатель сообщения. message: Текст сообщения."""

            start_time = time.time()
            answer_message = None

            while time.time() - start_time < timeout:

                await asyncio.sleep(random.uniform(1.2, 2.2))

                messages = await client.get_messages(bot_entity, limit=1)

                """get_messages возвращает список объектов telethon.types.Message, в нашем случае с одним объектом.
                Объект из себя представляет сообщение из чата."""

                if messages:

                    """ Обращаемся к списку объектов telethon.types.Message 
                    у каждого объекта есть атрибут message содержащий сообщение типа str"""

                    answer_message = messages[0].message 
                    break

            if answer_message is None:
                logger.warning(
                    f"Бот не ответил на команду '{command}' в течение {timeout} секунд.")
                file.close()
                return -1  # Ошибка: нет ответа

            logger.info(f"Ответ от бота: {answer_message}")
            if expected_answer is not None and answer_message != expected_answer:
                logger.warning(
                    f"Ошибка в реализации автомата: Когда тестировали с помощью {file_for_testing}:"
                    f"Ожидали '{expected_answer}', получили '{answer_message}'")
                file.close()
                return 0
            line = file.readline()
        file.close()
        logger.success("Успешно завершили тестирование по файлу через API...")
        return 1

    except FileNotFoundError:
        logger.error(f"\nНе найден файл '{file_for_testing}'\n")
        return -1
    except Exception as e:
        logger.error(f"Ошибка в communicating_with_bot: {e}")
        return -1


