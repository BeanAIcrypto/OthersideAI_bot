import re
from aiogram import types
from src.services.gpt_response_handler_text import response_answer
from src.keyboards.drating_inline_buttons_keyboard import drating_inline_buttons_keyboard
from aiogram.types import ChatActions
import logging
from db.dbworker import (get_user_limit,
                         update_user_limit,
                         add_history_entry)

from src.bot.bot_messages import MESSAGES, MESSAGES_ERROR
from dotenv import load_dotenv

from src.converter.image_processing import image_processing
from src.converter.translating_text_into_audio import generate_audio_tts
from src.services.clear_directory import clear_directory

load_dotenv()

logger = logging.getLogger(__name__)


def convert_markdown_to_markdownv2(text):
    try:
        text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)

        text = re.sub(r'### (.*?)\n', r'__\1__\n', text)

        special_chars = r'([\[\]\(\)~>#+\-=|{}.!])'

        text = re.sub(special_chars, r'\\\1', text)
    except Exception as e:
        logger.error(f"Ошибка перевода в markdownv2 {str(e)}")

    return text


async def process_user_message(user_id, user_name, text, language, history, prompt, bot, message = None, chat_id=None):
    try:
        logger.info(f"Вызов модели для пользователя {user_name} (ID: {user_id}) с запросом: {text}")
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.TYPING)
        await bot.send_chat_action(chat_id=user_id, action='typing')

        first_message = await bot.send_message(chat_id=user_id, text=MESSAGES["process_user_message"][language])
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatActions.TYPING)
        if prompt == 'image' :
            response = await image_processing(message, language, text, bot, user_id)
        else:
            response = await response_answer(user_id, text, language, history, prompt, bot)

        if not response:
            raise ValueError("Empty response received")

        logger.info(f"Сообщения от модели: {response}")
        assistant_response_id = add_history_entry(user_id, text, response)

        if chat_id == user_id:
            rating_keyboard = drating_inline_buttons_keyboard(assistant_response_id)
            rating_message = MESSAGES["rating_request"].get(language)
        else:
            rating_keyboard = None
            rating_message = ''

        response_with_rating = response + '\n' + rating_message

        try:
            formatted_text = convert_markdown_to_markdownv2(response_with_rating)
        except Exception as e:
            logger.error(f"Ошибка перевода текста в MarkdownV2: {e}")
            await bot.send_message(chat_id=user_id, text=MESSAGES_ERROR["markdown_error"][language])
            return

        await bot.send_message(
            chat_id=user_id,
            text=formatted_text,
            reply_markup=rating_keyboard,
            parse_mode="MarkdownV2"
        )

        audio_file_path, base_dir = await generate_audio_tts(response, user_id, bot, language='ru')
        with open(audio_file_path, "rb") as audio:
            await message.bot.send_voice(
                chat_id=message.chat.id,
                voice=types.InputFile(audio, filename="response.ogg"),
            )

        await clear_directory(base_dir)
        await bot.delete_message(chat_id=user_id, message_id=first_message.message_id)

        logger.info(f"Обработка сообщения от пользователя {user_name} завершена")
    except ValueError as ve:
        logger.error(f"Ошибка: {ve}")
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=first_message.message_id,
            text=MESSAGES_ERROR["error_response"][language]
        )
    except Exception as e:
        logger.error(f"Произошла ошибка обработки сообщения: {e}")
        await bot.send_message(chat_id=user_id, text=MESSAGES_ERROR["error_response"][language])

