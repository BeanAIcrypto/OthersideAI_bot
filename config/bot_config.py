import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.utils.cli import parse_arguments
import logging


logger = logging.getLogger(__name__)
load_dotenv()
args = parse_arguments()

def setup_bot():
    from src.bot import handlers

try:
    if not args.init:
        GPT_SECRET_KEY_FASOLKAAI = os.getenv("GPT_SECRET_KEY_FASOLKAAI")
        TG_TOKEN = os.getenv("TG_TOKEN")
        MODEL_GPT4 = "gpt-4o-mini"
        if not TG_TOKEN:
            logger.error("Отсутствует TG_TOKEN в переменных окружения. Завершение работы.")
            sys.exit(1)
        if not GPT_SECRET_KEY_FASOLKAAI:
            logger.error("Отсутствует GPT_SECRET_KEY_FASOLKAAI в переменных окружения. Завершение работы.")
            sys.exit(1)
        server = TelegramAPIServer.from_base('https://tgrasp.co')
        bot = Bot(token=TG_TOKEN, server=server)
        dp = Dispatcher(bot, storage=MemoryStorage(), run_tasks_by_default=True)

    else:
        logger.info('init flag был выбран, выполнение программы не требуется. Завершение работы.')
        sys.exit(0)

    setup_bot()

except Exception as e:
    logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
    sys.exit(1)
