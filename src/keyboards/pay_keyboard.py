from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
import logging


logger = logging.getLogger(__name__)


def pay_keyboard(url):
    try:
        button = [
            [InlineKeyboardButton('Pay', web_app=WebAppInfo(url=url))],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=button)
        return keyboard
    except Exception as e:
        logger.error(f'Ошибка создания клавиатуры подписки (InlineKeyboard): {str(e)}')