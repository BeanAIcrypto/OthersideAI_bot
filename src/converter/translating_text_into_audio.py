import os
import uuid
import logging
import asyncio
from openai import OpenAI

from db.dbworker import get_user_limit, update_user_limit
from src.services.count_token import count_total_tokens, count_tokens


OPENAI_API_KEY = os.getenv("GPT_SECRET_KEY_FASOLKAAI")
client = OpenAI(api_key=OPENAI_API_KEY)
logger = logging.getLogger(__name__)


async def convert_to_ogg_opus(input_path: str, output_path: str):
    """
    Конвертация аудиофайла в OGG/Opus с помощью FFmpeg.

    Args:
        input_path (str): Путь к входному аудиофайлу.
        output_path (str): Путь к выходному аудиофайлу.

    Raises:
        RuntimeError: Если FFmpeg завершается с ошибкой.
    """
    command = [
        "ffmpeg", "-y", "-i", input_path,
        "-filter:a", "atempo=1.30",
        "-c:a", "libopus", "-b:a", "64k", "-ar", "48000",
        output_path
    ]
    process = await asyncio.create_subprocess_exec(*command)
    await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {process.returncode}")
    logger.info(f"Аудио успешно конвертировано в OGG: {output_path}")


async def generate_audio_tts(text: str, user_id: int, bot, language: str = 'ru') -> (str, str):
    """
    Генерация аудио с использованием OpenAI TTS API.

    Args:
        text (str): Текст для озвучивания.
        user_id (int): ID телеграм-пользователя.
        bot: телеграм bot.
        language (str): Язык текста ("ru" или "en").

    Returns:
        str: Путь к финальному аудиофайлу в формате OGG.
    """
    try:
        voice_name = "shimmer"
        request_id = str(uuid.uuid4())

        total_tokens_input = count_tokens(text, model="gpt-4")
        logger.info(f"[USER_ID: {user_id}] Токены запроса: {total_tokens_input}")

        limit = get_user_limit(user_id)
        if limit - total_tokens_input <= 0:
            logger.warning("[USER_ID: {user_id}] Недостаточно токенов для генерации аудио.")
            await bot.send_message(
                chat_id=user_id,
                text="Недостаточно токенов для генерации аудио."
            )
            return None

        response = client.audio.speech.create(
            model="tts-1",
            voice=voice_name,
            input=text
        )

        audio_data = response.content

        base_dir = os.path.join("downloads", str(user_id), request_id)
        os.makedirs(base_dir, exist_ok=True)

        raw_audio_path = os.path.join(base_dir, "response_raw.mp3")
        with open(raw_audio_path, "wb") as audio_file:
            audio_file.write(audio_data)
        logger.info(f"Аудио успешно сохранено в файл: {raw_audio_path}")

        final_audio_path = os.path.join(base_dir, "response.ogg")
        await convert_to_ogg_opus(raw_audio_path, final_audio_path)

        os.remove(raw_audio_path)
        update_user_limit(user_id, limit-total_tokens_input)
        return final_audio_path, base_dir

    except Exception as e:
        logger.error(f"Ошибка при генерации аудио: {e}")
        return None
