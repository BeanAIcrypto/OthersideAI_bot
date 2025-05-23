from aiogram import executor
from config.bot_config import setup_bot, dp
from db.dbworker import create_db
from db.google_sheets import google_sheets
import logging
from src.bot.handlers import on_startup


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/LOG_file.log')
    ],
    force=True
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        google_sheets()
        logger.info('Google Sheets синхронизация запущена')

        create_db()
        logger.info('База данных создана')

        setup_bot()
        logger.info('Бот настроен и готов к работе')

        logger.info('Бот запущен и ожидает сообщения')
        executor.start_polling(dp, on_startup=on_startup)

    except Exception as e:
        logger.error(f'Ошибка при запуске бота: {str(e)}')
