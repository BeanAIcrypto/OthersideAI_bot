from src.bot.bot_messages import MESSAGES
from src.keyboards.language_keyboard import create_language_keyboard


async def language_selection(user_id, message):
    language = message.user_language
    if language == "None":
        await message.answer(MESSAGES['start'], reply_markup=create_language_keyboard())
        return
    return language
