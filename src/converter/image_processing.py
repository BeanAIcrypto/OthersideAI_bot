import os
import base64
from dotenv import load_dotenv
import tiktoken
import requests
import logging
from openai import OpenAI

from src.bot.promt import PROMTS

from db.dbworker import get_user_limit
from src.bot.bot_messages import MESSAGES

from db.dbworker import update_user_limit
from src.services.count_token import count_tokens

load_dotenv()
logger = logging.getLogger(__name__)

API_TOKEN = os.getenv('TG_TOKEN')
image_path = 'downloads/image.jpg'
client = OpenAI(api_key=os.getenv('GPT_SECRET_KEY_FASOLKAAI'))


def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

async def downloads_image(message, file_url):
    logger.info("URL изображения: %s", file_url)

    logger.info("Загрузка изображения...")
    response = requests.get(file_url)

    with open(image_path, 'wb') as f:
        f.write(response.content)

    if response.status_code != 200:
        logger.error("Ошибка загрузки изображения. Статус код: %s", response.status_code)
        await message.reply("Ошибка загрузки изображения. Попробуйте снова.")
        return

async def image_processing(message, language, question, bot, user_id):
    try:
        base64_image = encode_image(image_path)
        logger.info("Изображение успешно загружено.")

        user_query = message.caption if message.caption else "Опишите изображение."
        logger.info("Подготовка текста запроса: %s", user_query)

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": PROMTS['image'][language]}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            },
        ]

        logger.info("Подсчёт токенов в запросе...")
        encoding = tiktoken.encoding_for_model("gpt-4o")
        num_tokens = sum(len(encoding.encode(str(msg))) for msg in messages)
        limit = get_user_limit(user_id)
        if limit - num_tokens <= 0:
            logger.warning("Недостаточно токенов.")
            await bot.edit_message_text(text=MESSAGES["token_limit_exceeded"][language])
            return
        logger.info("Количество токенов в запросе: %d", num_tokens)

        logger.info("Отправка изображения и запроса в OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        total_tokens_response = count_tokens(response, model="gpt-4o")
        update_user_limit(user_id, limit - (num_tokens+total_tokens_response))
        logger.info("Запрос успешно отправлен в OpenAI.")

        response_text = response.choices[0].message.content
        response_tokens = len(encoding.encode(response_text))
        logger.info("Количество токенов в ответе: %d", response_tokens)

        if response_text:
            logger.info("Успешно получен ответ от OpenAI: %s", response_text)
            return response_text
        else:
            logger.warning("Ответ от OpenAI не содержит контента.")
            await message.reply("Ответ от OpenAI не содержит описания.")

    except Exception as e:
        logger.error("Ошибка обработки изображения: %s", str(e))
        await message.reply("Произошла ошибка при обработке изображения.")