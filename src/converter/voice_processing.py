import os
import uuid
import aiohttp
import logging

from db.dbworker import get_user_limit, update_user_limit
from src.services.count_token import count_vois_tokens
from src.services.limit_check import limit_check
from src.bot.bot_messages import MESSAGES, MESSAGES_ERROR
from src.services.clear_directory import clear_directory
from dotenv import load_dotenv
from src.services.count_token import count_tokens

load_dotenv()
logger = logging.getLogger(__name__)


async def transcribe_voice_message(language: str, message, user_id: int, user_name: str) -> str | None:
    """
    Транскрибирует голосовое сообщение пользователя.

    Args:
        language (str): Язык транскрипции.
        message: Объект сообщения Telegram.
        user_id (int): Идентификатор пользователя.
        user_name (str): Имя пользователя.

    Returns:
        str | None: Транскрибированный текст или None в случае ошибки.
    """
    request_id = str(uuid.uuid4())
    base_dir = os.path.join("downloads", str(user_id), request_id)
    os.makedirs(base_dir, exist_ok=True)
    audio_path = os.path.join(base_dir, "voice_question.mp3")

    logger.info(f"[USER_ID: {user_id}] Начало транскрипции голосового сообщения. Путь к файлу: {audio_path}")

    try:
        logger.info(f"[USER_ID: {user_id}] Скачивание голосового сообщения...")
        new_file = await message.voice.get_file()
        await new_file.download(destination_file=audio_path)
        logger.info(f"[USER_ID: {user_id}] Голосовое сообщение успешно скачано: {audio_path}")

        logger.info(f"[USER_ID: {user_id}] Подсчет токенов...")
        voice_token = await count_vois_tokens(audio_path)
        user_token = get_user_limit(user_id)
        limit = user_token - voice_token
        logger.info(
            f"[USER_ID: {user_id}] Токены - Аудио: {voice_token}, Лимит пользователя: {user_token}, Остаток: {limit}")

        if not await limit_check(limit, language, message, user_id, user_name):
            logger.warning(f"[USER_ID: {user_id}] Превышен лимит токенов.")
            await message.answer(MESSAGES_ERROR["limit_exceeded"][language])
            return None

        logger.info(f"[USER_ID: {user_id}] Отправка аудиофайла на транскрипцию...")
        transcript_text = await transcribe_voice(audio_path, language, message)
        logger.info(f"[USER_ID: {user_id}] Текст транскрипции: {transcript_text[:50]}")

        return transcript_text

    except ValueError as ve:
        logger.error(f"[USER_ID: {user_id}] Ошибка лимита или валидации: {ve}")
        await message.answer(MESSAGES_ERROR["limit_exceeded"][language])
        return None

    except OSError as oe:
        logger.error(f"[USER_ID: {user_id}] Ошибка файловой системы: {oe}")
        await message.answer(MESSAGES_ERROR["empty_transcription"][language])
        return None

    except aiohttp.ClientError as ce:
        logger.error(f"[USER_ID: {user_id}] Ошибка при запросе к API: {ce}")
        await message.answer(MESSAGES_ERROR["empty_transcription"][language])
        return None

    except Exception as e:
        logger.exception(f"[USER_ID: {user_id}] Неизвестная ошибка обработки аудио: {e}")
        await message.answer(MESSAGES_ERROR["empty_transcription"][language])
        return None

    finally:
        logger.info(f"[USER_ID: {user_id}] Очистка временной директории: {base_dir}")
        await clear_directory(base_dir)
        logger.info(f"[USER_ID: {user_id}] Директория очищена")


async def transcribe_voice(audio_path: str, language: str, message, user_id: int, bot) -> (str, str):
    """
    Выполняет транскрипцию голосового сообщения с использованием модели OpenAI Whisper.

    Args:
        audio_path (str): Путь к аудиофайлу.
        language (str): Язык для транскрипции.
        message: Сообщение Telegram для контекста.
        user_id (int): Уникальный идентификатор пользователя.
        bot: Telegram-бот.
    Returns:
        Optional[str]: Текст транскрипции или None в случае ошибки.

    Raises:
        ValueError: Если ключ API OpenAI не установлен или возникла ошибка запроса.
        Exception: Общая ошибка при выполнении транскрипции.
    """
    try:
        api_key = os.getenv("GPT_SECRET_KEY_FASOLKAAI")
        if not api_key:
            raise ValueError("Ключ API OpenAI не установлен.")

        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}

        async with aiohttp.ClientSession() as session:
            with open(audio_path, "rb") as audio_file:
                data = aiohttp.FormData()
                data.add_field("model", "whisper-1")
                data.add_field("file", audio_file, filename=os.path.basename(audio_path))

                async with session.post(url, headers=headers, data=data) as response:
                    if response.status != 200:
                        error_message = await response.text()
                        raise ValueError(f"Ошибка запроса: {response.status} - {error_message}")

                    result = await response.json()
                    transcript_text = result.get("text")
                    if transcript_text:
                        token_count = count_tokens(transcript_text, model="gpt-4")
                        limit = get_user_limit(user_id)
                        if limit - token_count <= 0:
                            logger.warning("Недостаточно токенов.")
                            await bot.edit_message_text(text=MESSAGES["token_limit_exceeded"][language])
                            return
                        update_user_limit(user_id, limit - token_count)
                        logger.info(f"Транскрибированный текст содержит {token_count} токенов.")
                        logger.info(f"лимит пользователя: {limit - token_count}")

                    else:
                        logger.warning("Транскрипция вернула пустой текст.")
                        return None, 0

                    return transcript_text, token_count

    except ValueError as ve:
        logger.error(f"Ошибка валидации данных: {ve}")
        await message.answer("Произошла ошибка при проверке API ключа или данных.")
        return None

    except aiohttp.ClientError as ce:
        logger.error(f"Ошибка соединения с API OpenAI: {ce}")
        await message.answer("Произошла ошибка подключения к сервису транскрипции.")
        return None

    except Exception as e:
        logger.error(f"Ошибка транскрипции: {e}")
        await message.answer("Произошла ошибка при обработке аудиофайла.")
        return None
