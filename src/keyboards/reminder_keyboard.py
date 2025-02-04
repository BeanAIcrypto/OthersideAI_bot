from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.bot.bot_messages import MESSAGES


def get_reminder_keyboard(language):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(MESSAGES['strategy_investment'][language], callback_data="strategy_investment"),
        InlineKeyboardButton(MESSAGES['improve_portfolio'][language], callback_data="improve_portfolio")
    )
    return keyboard