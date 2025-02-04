from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import logging
logger = logging.getLogger(__name__)


def check_subscriptions_keyboard(language) -> InlineKeyboardMarkup:
    channel_link = os.getenv("CHANNEL_LINK")

    if not channel_link:
        logger.error("Переменная окружения 'CHANNEL_LINK' не установлена")

    if language == "ru":
        buttons = [
            [InlineKeyboardButton(text='Подписаться', url=channel_link)],
        ]
    elif language == "en":
        buttons = [
            [InlineKeyboardButton(text='Subscribe', url=channel_link)],
        ]
    else:
        logger.warning(f"Неизвестный язык: {language}")
        raise ValueError(f"Unsupported language: {language}")

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

