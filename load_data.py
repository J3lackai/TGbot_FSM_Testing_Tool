import configparser as conf
import os
from loguru import logger
from cryptography.fernet import Fernet
from testing_bots import beautiful_exit, generate_key

def get_data_from_env() -> tuple[int, str, str, str, str | None]:

    if not os.path.exists(".env"):
        message = "Создайте файл '.env' в директории запуска программы для тестирования, с полями \
                    TELEGRAM_API_ID=\n TELEGRAM_API_HASH= \n PHONE= \n ENCRYPTED_SESSION=\n \
                    и заполните их, поле ENCRYPTED_SESSION заполнять не нужно. \
                    Поле PHONE это номер телефона привязанный к действующему аккаунту Телеграма\
                    с помощью которого производится вход в telethon, для тестирования ботов \
                    TELEGRAM_API_ID и TELEGRAM_API_HASH берутся из аккаунта телеграм."
        logger.critical("Ошибка: не найден необходимый файл '.env' в директории")
        logger.info(message)
        raise FileNotFoundError(message)
    api_id_str = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("PHONE")
    encryption_key = os.environ.get('ENCRYPTION_KEY')
    encrypted_session = os.getenv('ENCRYPTED_SESSION')
    if not all([api_id_str, api_hash, phone]):
        logger.critical(
            "Ошибка: Не найдены TELEGRAM_API_ID, TELEGRAM_API_HASH или PHONE в .env или переменных окружения.")
        raise ValueError("Необходимые переменные окружения не найдены.")
    if encrypted_session and not encryption_key:
        # Эта ситуация не должна возникнуть, если предыдущая проверка пройдена, но оставим для ясности
        logger.critical("Ошибка: Найдена зашифрованная сессия (ENCRYPTED_SESSION), "
                        "но отсутствует ключ шифрования (ENCRYPTION_KEY) в системных переменных окружения.")
        raise ValueError("Отсутствует ключ шифрования для существующей сессии.")
    elif not encryption_key:
        logger.warning("Ключ шифрования ENCRYPTION_KEY не найден в системных переменных окружения.")
        encryption_key = generate_key()
        logger.warning(f"Сгенерирован НОВЫЙ ключ шифрования")
        logger.warning("ВНИМАНИЕ: Этот ключ действителен только для текущего запуска. \
                       Чтобы использовать зашифрованную сессию в будущем, установите этот ключ \
                       как СИСТЕМНУЮ переменную окружения ENCRYPTION_KEY на вашем компьютере и перезапустите скрипт. ")
        
        """ Устанавливаем сгенерированный ключ в os.environ для текущего процесса,
        чтобы остальная часть кода могла его использовать.
        Это НЕ делает его постоянной системной переменной. """

        os.environ['ENCRYPTION_KEY'] = encryption_key
    if not api_id_str.isdigit():
        logger.critical(
            f"Ошибка: TELEGRAM_API_ID должен быть числом.")
        raise ValueError("TELEGRAM_API_ID должен быть числом.")
    else:
        api_id = int(api_id_str)
    return api_id, api_hash, phone, encryption_key, encrypted_session

def get_data_from_conf(path = "config.ini") -> tuple[int, str, tuple[str], list[bool], tuple[str]]:

    def ensure_right_config(path = "config.ini") -> conf.ConfigParser:

        config = conf.ConfigParser()
        if not os.path.exists("config.ini", encoding = 'utf-8'): #Проверяем есть ли конфиг в директории скрипта
            logger.warning("В директории отсутствует 'config.ini', создаём его...")
            write_default_config(path) #Если нет - создаём
        try:
            config.read(path)
        except conf.Error as e:
            logger.warning(f"Ошибка при чтении файла конфигурации: {e}.\
                           Заменяем конфигурацию на значения по умолчанию.")
            # Даже если произошла ошибка при чтении, все равно перезаписываем файл
            write_default_config(path)
            return

        if not config.has_section('Main') or  not config.has_section('Telegram'): #Проверяем что есть нужные секции
            logger.warning("Отсутствует секция 'Main' или 'Telegram'. Заменяем конфигурацию на значения по умолчанию.")
            write_default_config(path)
        else:
            logger.debug("Нашли секции 'Main' и 'Telegram' в файле-конфиге...")


    def write_default_config(path):# Перезаписывает файл-конфиг, либо создаёт его если его нет
        default_config = """
        [Main]
        # Уровень логирования из ["TRACE", "DEBUG", "INFO"] указывать без кавычек
        # Запретил ставить уровни выше INFO потому что теряется слишком много информации, TRACE не используется в коде
        level_logging=INFO \n
        # Тесты в формате: namefile.txt[1], namefile.txt[2], ..., namefile.txt[n] // [i] не нужно писать
        tests=graph.txt, wasil.txt, hybrid.txt \n
        # Как долго ждать ответа от бота в сек
        wait_time = 10 \n
        [Telegram]
        # Телеграм-имена ботов которые тестируются, нужно заполнить в формате: @name_bot[1], @name_bot[2], ..., @name_bot[n] // [i] не нужно писать
        bots=
        """
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(default_config)
            logger.info(f"Файл конфигурации '{path}' успешно перезаписан значениями по умолчанию.")
        except IOError as e:
            logger.info(f"Ошибка при записи в файл '{path}': {e}")

    config = ensure_right_config(path = path)
    main_conf = config['Main']
    tg_conf = config['Telegram']
    if tg_conf["bots"] == "":
        logger.info("Конфигурационный файл 'config.ini' ещё не настроен. Перед запуском этого скрипта вы должны добавить в него \
                    имена тестируемых телеграм-ботов.")
        beautiful_exit()
    # Время ожидания ответа от бота

    wait_str = main_conf["wait_time"]
    if not wait_str.isdigit() or not 0 <= int(wait_str) <= 60:
        logger.warning("Ошибка: Неправильно указан wait_time в конфиге, использовано дефолтное значение 10 секунд")
        wait = 10
    else:
        wait = int(wait_str)
    # Преобразуем строковый уровень логирования в числовой
    lvl_log = main_conf["level_logging"].upper()
    # Проверяем допустимость уровня логирования
    # Запретил ставить уровни выше INFO потому что теряется слишком много информации
    valid_log_levels = ["TRACE", "DEBUG", "INFO"]
    if lvl_log not in valid_log_levels:
        logger.warning(
            f"Недопустимый уровень логирования '{lvl_log}', используем INFO")
        lvl_log = "INFO"  # Используем INFO по умолчанию
    
    # Список тестов полученный из файла-конфига.
    list_tests = main_conf['tests'].replace(
        " ", "").split(',')  # Правильная обработка запятых
    for test in list_tests:
        if not test.lower().endswith(".txt"):
            logger.critical(
                "Ошибка: Неправильные названия файлов для тестирования, должно быть в формате:\
                      namefile[1], namefile[2], ..., namefile[n] // [i] не нужно писать")
            raise ValueError(
                "Ошибка: Неправильные названия файлов для тестирования, должно быть в формате:\
                      namefile[1], namefile[2], ..., namefile[n] // [i] не нужно писать")
        if not os.path.exists(test):
            logger.critical(
                f"Ошибка: Файла с указанным именем: {test} нет в текущей директории, проверьте что файл с таким названием там есть.")
            raise ValueError(
                f"Ошибка: Файла с указанным именем: {test} нет в текущей директории, проверьте что файл с таким названием там есть.")

    list_res = [False] * len(list_tests)  # Список результатов этих тестов

    # Список ботов полученный из файла-конфига.
    list_bots = tg_conf["bots"].replace(" ", "").split(',')
    for bot in list_bots:
        if not bot.startswith("@"):
            logger.critical(
                "Ошибка: Неправильные названия ботов для тестирования, должно быть в формате:\
                      @name_bot[1], @name_bot[2], ..., @name_bot[n] // [i] не нужно писать")
            raise ValueError(
                "Ошибка: Неправильные названия ботов для тестирования, должно быть в формате:\
                      @name_bot[1], @name_bot[2], ..., @name_bot[n] // [i] не нужно писать")

    if not list_bots:
        logger.critical(
            "Ошибка конфига: bots должен содержать имя хотя бы одного бота. @name_bot[1], @name_bot[2], ..., @name_bot[n] // [i] не нужно писать")
        raise ValueError(
            "Ошибка конфига: bots должен содержать имя хотя бы одного бота. @name_bot[1], @name_bot[2], ..., @name_bot[n] // [i] не нужно писать")
    return wait, lvl_log, tuple(list_tests), list_res, tuple(list_bots)