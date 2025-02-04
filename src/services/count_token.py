import tiktoken
import logging
import asyncio
from typing import Union, List

logger = logging.getLogger(__name__)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Подсчет количества токенов в тексте.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        logger.error(f"Ошибка подсчета токенов: {str(e)}")
        return 0


def count_total_tokens(history: List[dict], user_input: str, model: str = "gpt-4") -> int:
    """
    Подсчет общего количества токенов для истории и запроса пользователя.
    """
    total_tokens = 0

    for entry in history:
        if 'question' in entry and 'response' in entry:
            total_tokens += count_tokens(entry['question'], model=model)
            total_tokens += count_tokens(entry['response'], model=model)

    total_tokens += count_tokens(user_input, model=model)

    return total_tokens


async def get_audio_duration(audio_file: str) -> float:
    """
    Получает продолжительность аудиофайла с помощью ffprobe.
    """
    try:
        logger.info(f"Запуск ffprobe для файла: {audio_file}")
        process = await asyncio.create_subprocess_exec(
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            duration = float(stdout.strip())
            logger.info(f"Продолжительность аудиофайла: {duration} сек.")
            return duration

        logger.error(f"Ошибка ffprobe: {stderr.decode().strip()}")
        return 0
    except Exception as e:
        logger.error(f'Ошибка при получении продолжительности аудиофайла: {e}')
        return 0


async def count_vois_tokens(audio_parts: Union[str, List[str]]) -> int:
    """
    Подсчет количества токенов для аудиофайлов.
    """
    try:
        # Приводим к списку, если передана строка
        if isinstance(audio_parts, str):
            audio_parts = [audio_parts]

        logger.info(f"Файлы для подсчета токенов: {audio_parts}")
        durations = await asyncio.gather(*[get_audio_duration(part) for part in audio_parts])

        total_duration = sum(durations)
        token_per_minute = 400
        estimated_tokens = (total_duration / 60) * token_per_minute

        logger.info(f"Общая длительность: {total_duration} сек. Примерное количество токенов: {estimated_tokens}")
        return int(estimated_tokens)
    except Exception as e:
        logger.error(f'Ошибка при подсчете токенов для аудио: {e}')
        return 0
