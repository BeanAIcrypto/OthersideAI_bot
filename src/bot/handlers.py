import os
import re
import uuid

import magic
from aiogram import Dispatcher, types
from src.services.limit_check import limit_check
from aiogram.types import ContentTypes, InputFile
from aiogram.types import ContentType
from config.bot_config import bot, dp
from src.services.analytics_creating_target import analytics_creating_target
from src.converter.document_processing import text_extraction_from_a_document
from src.keyboards.language_keyboard import create_language_keyboard
from src.services.language_selection import language_selection
from src.services.process_user_message import process_user_message
from src.converter.voice_processing import transcribe_voice_message
from src.converter.link_processing import link_processing
from src.converter.you_tube_link_processing import you_tube_link_processing
from db.dbworker import (
    create_user,
    update_dialog_score,
    update_user_language,
    get_user_history,
    get_user_limit,
    get_user_training,
    update_user_training_status,
    update_user_training_last_message,
    get_user_training_last_message,
    update_get_user_keyboard,
)
from src.bot.bot_messages import MESSAGES
from src.bot.promt import  PROMTS
from db.background_functions import start_background_tasks
import asyncio
from src.services.delete_keyboard import remove_keyboards_from_messages
from dotenv import load_dotenv
import logging
from src.converter.image_processing import downloads_image
from src.services.clear_directory import clear_directory

load_dotenv()

logger = logging.getLogger(__name__)

API_TOKEN = os.getenv('TG_TOKEN')
image_path = 'downloads/image.jpg'

load_dotenv()

logger = logging.getLogger(__name__)
mime = magic.Magic(mime=True)
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")


async def on_startup(dispatcher: Dispatcher):
    try:
        asyncio.create_task(start_background_tasks(dp.bot))
        logger.info('Фоновая задача напоминания запущена')
        await set_default_commands(dp.bot)
        await dp.bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске on_startup: {str(e)}")


async def set_default_commands(dp: Dispatcher):
    try:
        await bot.set_my_commands([
            types.BotCommand("language", "Choose your language/ Выберите свой язык"),
            types.BotCommand("donate", "Donate/ Оформить донат"),
        ])
    except Exception as e:
        logger.error(f"Произошла ошибка в создании меню: {str(e)}")


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    text = message.text
    update_user_training_last_message(user_id, text)
    logger.info(f"Команда /start от пользователя {user_name} (ID: {user_id})")
    name_keyboard = 'language'
    try:
        create_user(user_id, user_name)
        logger.info(f"Пользователь {user_name} (ID: {user_id}) добавлен в базу данных")
        sent_message = await message.answer(MESSAGES["start"], reply_markup=create_language_keyboard())
        update_get_user_keyboard(user_id, name_keyboard, sent_message.message_id)
        logger.info(f"Сообщение с выбором языка отправлено пользователю {user_name}")
        await analytics_creating_target(user_id, user_name, target_start_id=10339, value=None, unit=None)
    except Exception as e:
        logger.error(f"Ошибка в обработчике команды /start: {e}")
        await message.reply(MESSAGES['start_error'])


@dp.message_handler(commands=['donate'])
async def donate(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.username

    try:
        language = await language_selection(user_id, message)
        if not language or language == "None":
            raise KeyError(f"Язык не установлен для пользователя {user_name} (ID: {user_id})")

        await message.answer(
            MESSAGES["donate"][language],
            parse_mode="MarkdownV2"
        )
        logger.info(f"Ссылка на оплату отправлена пользователю {user_name} (ID: {user_id})")

    except KeyError as ke:
        logger.error(f"Ошибка языка для пользователя {user_name} (ID: {user_id}): {str(ke)}")

    except ValueError as ve:
        logger.error(f"Неподдерживаемый язык для пользователя {user_name} (ID: {user_id}): {str(ve)}")

    except Exception as e:
        logger.error(f"Неизвестная ошибка в обработчике команды /donate для {user_name} (ID: {user_id}): {str(e)}")


# Выбор языка
@dp.message_handler(commands=["language"])
async def language_choice(message: types.Message):
    user_id = message.from_user.id
    name_keyboard = 'language'
    sent_message = await message.answer(MESSAGES["start"], reply_markup=create_language_keyboard())
    update_get_user_keyboard(user_id, name_keyboard, sent_message.message_id)


@dp.message_handler(content_types=ContentType.VOICE)
async def voice(message: types.Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_name = message.from_user.username
        history = get_user_history(user_id)

        language = await language_selection(user_id, message)
        if not language:
            return

        limit = get_user_limit(user_id)
        if not await limit_check(limit, language, message, user_id, user_name):
            return

        text = await transcribe_voice_message(language, message, user_id, user_name)
        if not text:
            return

        logger.info(f"Пользователь {user_name} (ID: {user_id}) отправил голосовое сообщение: {text}")

        await process_user_message(
            user_id=user_id,
            user_name=user_name,
            text=text,
            language=language,
            history=history,
            prompt=str(PROMTS['text_voice'][language]),
            bot=bot,
            chat_id=chat_id,
            message=message
        )

    except Exception as e:
        logger.error(f"Ошибка: {e}, сообщение: {message}")


@dp.message_handler(lambda message: re.search(
    r'https:\/\/(www\.)?(youtube\.com|youtu\.be)\/[^\s]+',
    message.text, ))
async def you_tube_link_handler(message: types.Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_name = message.from_user.username
        text = message.text

        language = await language_selection(user_id, message)
        if not language:
            return

        limit = get_user_limit(user_id)
        if not await limit_check(limit, language, message, user_id, user_name):
            return

        url_match = re.search(r'https:\/\/(www\.)?(youtube\.com|youtu\.be)\/[^\s]+', text)
        if url_match:
            url = url_match.group(0)
        else:
            await message.answer(MESSAGES["link_handler"][language])
            return

        logger.info(f"Сообщение пользователя {text}")
        logger.info(f"От пользователя {user_id} получен текст с ссылкой: {url}")
        history = get_user_history(user_id)
        awaiting_message = await message.answer(MESSAGES["link_handler_await"][language])
        link_text = await you_tube_link_processing(url, user_id, language, message, bot)

        if not link_text:
            await message.answer(MESSAGES["link_handler_error_data"][language])
            return

        logger.info(f"Из файла {url} получен текст: {link_text[:1000]}")

        question = (f'Запрос пользователя: {text}. '
                    f'Пользователь предоставил ссылку: "{url}". Содержание ссылки:\n{link_text}')

        logger.info(f"Пользователь {user_name} (ID: {user_id}) отправил сообщение: {question[:1000]}")

        await process_user_message(
            user_id=user_id,
            user_name=user_name,
            text=question,
            language=language,
            history=history,
            prompt=str(PROMTS['you_tube_link'][language]),
            bot=bot,
            chat_id=chat_id,
            message=message
        )
        await awaiting_message.delete()
    except Exception as e:
        logger.error(f"Ошибка: {e}, сообщение: {message}")


@dp.message_handler(lambda message: re.search(r'https?:\/\/[^\s]+', message.text))
async def link_handler(message: types.Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_name = message.from_user.username
        text = message.text

        language = await language_selection(user_id, message)
        if not language:
            return

        limit = get_user_limit(user_id)
        if not await limit_check(limit, language, message, user_id, user_name):
            return

        url_match = re.search(r'https?:\/\/[^\s]+', text)
        if url_match:
            url = url_match.group(0)
        else:
            await message.answer(MESSAGES["link_handler"][language])
            return

        logger.info(f"Сообщение пользователя {text}")
        logger.info(f"От пользователя {user_id} получен текст с ссылкой: {url}")

        history = get_user_history(user_id)

        awaiting_message = await message.answer(MESSAGES["link_handler_await"][language])

        link_text = await link_processing(url)

        if link_text:
            logger.info(f"Из файла {url} получен текст: {link_text[:1000]}")
        else:
            await message.answer(MESSAGES["link_handler_error_data"][language])
            return

        question = (f'Запрос пользователя: {text}.'
                    f'Пользователь предоставил ссылку: "{url}". Содержание ссылки:\n{link_text}')

        logger.info(f"Пользователь {user_name} (ID: {user_id}) отправил сообщение: {question[:1000]}")

        await process_user_message(
            user_id=user_id,
            user_name=user_name,
            text=question,
            language=language,
            history=history,
            prompt=str(PROMTS['link'][language]),
            bot=bot,
            chat_id=chat_id,
            message=message
        )
        await awaiting_message.delete()
    except Exception as e:
        logger.error(f"Ошибка: {e}, сообщение: {message}")


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def text_handler(message: types.Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_name = message.from_user.username
        text = message.text
        history = get_user_history(user_id)
        language = await language_selection(user_id, message)
        if not language:
            return

        limit = get_user_limit(user_id)
        if not await limit_check(limit, language, message, user_id, user_name):
            return

        logger.info(f"Пользователь {user_name} (ID: {user_id}) отправил сообщение: {text}")

        await process_user_message(
            user_id=user_id,
            user_name=user_name,
            text=text,
            language=language,
            history=history,
            prompt=str(PROMTS['text_voice'][language]),
            bot=bot,
            chat_id=chat_id,
            message=message
        )
    except Exception as e:
        logger.error(f"Ошибка: {e}, сообщение: {message}")


@dp.message_handler(content_types=ContentType.DOCUMENT)
async def document_handler(message: types.Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        request_id = str(uuid.uuid4())
        user_name = message.from_user.username

        base_dir = os.path.join("downloads", str(user_id), request_id)
        os.makedirs(base_dir, exist_ok=True)

        document = message.document
        file_name = document.file_name
        file_path = os.path.join(base_dir, file_name)

        file_info = await message.bot.get_file(document.file_id)
        await file_info.download(destination_file=file_path)
        logger.info(f"Файл {file_name} загружен в папку downloads")

        history = get_user_history(user_id)
        user_text = message.caption if message.caption else ''
        logger.info(f"Сообщение пользователя {user_text}")
        logger.info(f"От пользователя {user_id} получен документ: {file_name}")

        logger.info(f"Филе с именем {file_name} загружен в папку: downloads")

        language = await language_selection(user_id, message)
        if not language:
            return

        limit = get_user_limit(user_id)
        if not await limit_check(limit, language, message, user_id, user_name):
            return

        text_extraction_function = text_extraction_from_a_document[document.mime_type]

        awaiting_message = await message.answer(MESSAGES["link_handler_await"][language])

        if text_extraction_function:
            text_document = text_extraction_function(file_path)
            if not text_document:
                await message.answer(MESSAGES["document_handler_error"][language])
                return
            logger.info(f"Из файла {file_name} получен текст: {text_document[:1000]}")
        else:
            await message.answer(MESSAGES["document_handler_not_found"][language])
            return

        question = (f'Подпись к документу или(и) запрос пользователя: {user_text}.'
                    f'Название документа: "{file_name}". Содержание документа\n :{text_document}')

        logger.info(f"Пользователь {user_name} (ID: {user_id}) отправил сообщение: {question[:1000]}")
        await process_user_message(
            user_id=user_id,
            user_name=user_name,
            text=question,
            language=language,
            history=history,
            prompt=str(PROMTS['document'][language]),
            bot=bot,
            chat_id=chat_id,
            message=message
        )
        await awaiting_message.delete()
        await clear_directory(base_dir)
        logger.info(f"Файл {file_name} был удален после обработки.")

    except Exception as e:
        logger.error(f"Ошибка: {e}, сообщение: {message}")


@dp.message_handler(content_types=ContentTypes.PHOTO)
async def handle_photo(message: types.Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_name = message.from_user.username
        text = message.caption if message.caption else ''
        history = get_user_history(user_id)
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_path = file_info.file_path
        file_url = f'https://api.telegram.org/file/bot{API_TOKEN}/{file_path}'

        language = await language_selection(user_id, message)
        if not language:
            return
        limit = get_user_limit(user_id)

        if not await limit_check(limit, language, message, user_id, user_name):
            return
        await downloads_image(message, file_url)

        question = (f'Подпись к картинке или(и) запрос пользователя: {text}.'
                    f'URL картинки: "{file_url}".')

        await process_user_message(
            user_id=user_id,
            user_name=user_name,
            text=question,
            language=language,
            history=history,
            prompt='image',
            bot=bot,
            message=message,
            chat_id=chat_id
        )

    except Exception as e:
        logger.error(f"Ошибка: {e}, сообщение: {message}")


@dp.message_handler(content_types=ContentTypes.ANY)
async def all_updates_handler(message: types.Message):
    """Обработчик остальных сообщений от пользователя"""
    user_id = message.from_user.id
    user_name = message.from_user.username

    logger.info(
        f"Пользователь {user_name} (ID: {user_id}) отправил сообщение неизвестного типа: {message.content_type}")

    language = await language_selection(user_id, message)
    if not language:
        return

    await message.answer(MESSAGES["all_updates_handler"][language])
    logger.info(f"Ответ отправлен пользователю {user_name} (ID: {user_id}) на неизвестное сообщение")


@dp.callback_query_handler(lambda c: c.data.startswith("rate_"))
async def process_callback_rating(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.username
    language = callback_query.user_language

    if language == "None":
        logger.warning(f"Язык не установлен для пользователя {user_name} (ID: {user_id})")
        await bot.send_message(user_id, MESSAGES["start"])
        return

    logger.info(f"Обработка колбэка с оценкой от пользователя {user_name} (ID: {user_id}): {callback_query.data}")

    try:
        data = callback_query.data.split("_")
        rating = str(data[1])
        response_id = int(data[2])

        logger.info(f"Пользователь {user_name} (ID: {user_id}) выбрал оценку: {rating} для ответа {response_id}")

        if language:
            await bot.send_message(user_id, MESSAGES["process_callback_rating"][language])
        else:
            logger.warning(f"Неопределённый язык для пользователя {user_name} (ID: {user_id})")
            await bot.send_message(user_id, MESSAGES["start"])
            return

        await bot.edit_message_reply_markup(
            callback_query.message.chat.id,
            callback_query.message.message_id,
            reply_markup=None
        )

        update_dialog_score(rating, response_id)
        logger.info(
            f"Оценка {rating} сохранена для сообщения с ID {response_id} пользователя {user_name} (ID: {user_id})")

        logger.info(f"Клавиатура оценки удалена для пользователя {user_name} (ID: {user_id})")

        await bot.answer_callback_query(callback_query.id)

    except Exception as e:
        logger.error(f"Ошибка при обработке колбэка оценки для пользователя {user_name} (ID: {user_id}): {str(e)}")
        await bot.send_message(user_id, MESSAGES["process_callback_rating_error"][language])


@dp.callback_query_handler(lambda call: call.data in ["🇬🇧 English", "🇷🇺 Русский"])
async def handle_language_choice_callback(callback_query: types.CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        user_name = callback_query.from_user.username
        selected_language = callback_query.data
        user_language = 'None'

        logger.info(f"Пользователь {user_name} (ID: {user_id}) выбрал язык: {selected_language}")

        if selected_language == "🇬🇧 English":
            user_language = 'en'
            await bot.send_message(user_id, MESSAGES['handle_language_choice_first_message'][user_language])
            logger.info(f"Язык пользователя {user_name} (ID: {user_id}) обновлен на английский")
        elif selected_language == "🇷🇺 Русский":
            user_language = 'ru'
            await bot.send_message(user_id, MESSAGES["handle_language_choice_first_message"][user_language])
            logger.info(f"Язык пользователя {user_name} (ID: {user_id}) обновлен на русский")

        await remove_keyboards_from_messages(bot, user_id, name_keyboard='language')
        update_user_language(user_id, user_language)
        await bot.answer_callback_query(callback_query.id)

    except Exception as e:
        logger.error(f"Ошибка при выборе языка для пользователя {user_name} (ID: {user_id}): {str(e)}")
        await bot.send_message(user_id, MESSAGES["handle_language_choice_error"])


@dp.callback_query_handler(lambda c: c.data in ["strategy_investment", "improve_portfolio"])
async def process_callback_button(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    language = callback_query.user_language
    if callback_query.data == "strategy_investment":
        await bot.send_message(user_id, MESSAGES['process_callback_button_strategy_investment'][language], parse_mode="MarkdownV2")

    elif callback_query.data == "improve_portfolio":
        await bot.send_message(user_id, MESSAGES['process_callback_button_improve_portfolio'][language], parse_mode="MarkdownV2")

    await callback_query.answer()


@dp.my_chat_member_handler()
async def handle_chat_member_update(update: types.ChatMemberUpdated):
    user_id = update.from_user.id
    user_name = update.from_user.first_name if update.from_user.first_name else "Unknown"

    if update.new_chat_member.status == 'kicked':
        await analytics_creating_target(user_id, user_name, target_start_id=10341, value=None, unit=None)
        logger.info(f"Пользователь {user_id} ({user_name}) заблокировал бота")

    elif update.new_chat_member.status == 'left':
        await analytics_creating_target(user_id, user_name, target_start_id=10341, value=None, unit=None)
        logger.info(f"Пользователь {user_id} ({user_name}) удалил бота")
