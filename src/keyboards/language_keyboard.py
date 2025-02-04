from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging


logger = logging.getLogger(__name__)

def create_language_keyboard() -> InlineKeyboardMarkup:
    try:
        buttons = [
            [InlineKeyboardButton("🇬🇧 English", callback_data="🇬🇧 English")],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="🇷🇺 Русский")]
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        logger.info("Клавиатура для выбора языка успешно создана")
        return keyboard
    except Exception as e:
        logger.error(f"Ошибка при создании клавиатуры для выбора языка: {str(e)}")
        return InlineKeyboardMarkup()

