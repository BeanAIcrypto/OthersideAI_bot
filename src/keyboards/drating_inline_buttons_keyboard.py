from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

logger = logging.getLogger(__name__)


def drating_inline_buttons_keyboard(response_id: int) -> InlineKeyboardMarkup:
    try:
        buttons = [
            [InlineKeyboardButton(text=str(i), callback_data=f"rate_{i}_{response_id}") for i in ['👎', '😐', '👍']],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        logger.info(f"Инлайн-клавиатура для оценки создана для response_id: {response_id}")
        return keyboard
    except Exception as e:
        logger.error(f"Ошибка при создании инлайн-клавиатуры для response_id {response_id}: {str(e)}")
        return InlineKeyboardMarkup()
