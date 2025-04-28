from testing_bots import testing_bots
from loguru import logger
from keyboard import wait


def beautiful_exit():
    print("Нажмите 'Enter' для завершения программы.")
    wait("enter")
    exit()


def print_results_in_table(list_res, tuple_tests, bot_username_tg):

    name_method_header = "Файл для тестирования"
    result_testing_header = "Обнаружены ли ошибки в реализации автомата?"

    # Определяем максимальную ширину для первого столбца
    col1_width = max(max((len(i) for i in tuple_tests),
                     default=0), len(name_method_header)) + 2

    # Определяем ширину для второго столбца (заголовок или True/False)
    # Можно сделать фиксированной или взять максимум от заголовка и "False" (самое длинное значение)
    col2_width = len(result_testing_header) + 2

    # '<' - выравнивание по левому краю, '>' - по правому, '^' - по ширине
    
    message_table = f"{name_method_header:<{col1_width}}| {result_testing_header:<{col2_width}}"

    logger.success(f"Выполнено тестирование для бота: {bot_username_tg}")
    logger.success("-" * (col1_width + col2_width)) # Разделитель строк
    logger.success(message_table)

    for i in range(len(tuple_tests)):

        logger.success("-" * (col1_width + col2_width))
        # Имя файла и результат - по ширине
        result_str = str(not list_res[i])
        logger.success(
            f"{tuple_tests[i]:^{col1_width}}| {result_str:^{col2_width}}")
        
def main():
    try:
        list_res, tuple_tests, bot_username_tg = testing_bots()
        if None in (list_res, tuple_tests, bot_username_tg):
            logger.error("Тестирование завершено с ошибками.")
        else:
            print_results_in_table(
                list_res=list_res, tuple_tests=tuple_tests, bot_username_tg=bot_username_tg)      
    except:
        pass
    finally:   
        beautiful_exit()

if __name__ == "__main__":
    main()
