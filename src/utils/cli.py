import argparse
import sys


def parse_arguments():
    """
    Функция для анализа входных параметров с помощью argparse.
    Возвращает объект с аргументами командной строки.
    """
    try:
        parser = argparse.ArgumentParser(description="Парсинг входных параметров")

        parser.add_argument("--init", default=False, action="store_true",
                            help="Флаг, указывающий на инициализацию без реального выполнения")

        args = parser.parse_args()

        return args

    except argparse.ArgumentError as e:
        print(f"Ошибка при парсинге аргументов: {e}")
        sys.exit(1)

