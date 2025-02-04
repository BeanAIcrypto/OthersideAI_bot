import os
from aiogram import Bot
from aiogram.types import ChatMember
from aiogram.utils.exceptions import ChatNotFound, Unauthorized
from src.keyboards.check_subscriptions_keyboard import check_subscriptions_keyboard
import logging


logger = logging.getLogger(__name__)


CHANNEL_ID = os.getenv("CHANNEL_ID")

async def check_subscription(user_id: int, bot: Bot) -> bool:
    try:
        if not CHANNEL_ID:
            logger.error("CHANNEL_ID не установлен. Проверьте переменные окружения.")
            return False

        chat_member: ChatMember = await bot.get_chat_member(CHANNEL_ID, user_id)
        logger.info(f"Пользователь {user_id} статус {chat_member.status}.")
        if chat_member.status in ['member', 'administrator', 'creator']:
            logger.info(f"Пользователь {user_id} подписан на канал.")
            return True
        else:
            logger.info(f"Пользователь {user_id} не подписан на канал. Статус: {chat_member.status}")
            return False

    except ChatNotFound:
        logger.error("Канал не найден. Проверьте CHANNEL_ID и убедитесь, что бот добавлен в канал.")
        return False
    except Unauthorized:
        logger.error("Бот не имеет доступа к каналу. Проверьте права доступа бота.")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return False


async def subscription(user_id, language, message, bot):
    try:
        logger.info(f"Проверка подписки для пользователя {user_id} на языке {language}")

        if not await check_subscription(user_id, bot):
            sub_message = {
                "ru": f"Подпишитесь на наш <a href='{os.getenv('CHANNEL_LINK')}'>Telegram-канал</a> 😎",
                "en": f"Please subscribe to our <a href='{os.getenv('CHANNEL_LINK')}'>Telegram channel</a> 😎"
            }.get(language)

            logger.info(f"Пользователь {user_id} не подписан, отправлено сообщение с просьбой подписаться.")
            await message.reply(sub_message, parse_mode='HTML', reply_markup=check_subscriptions_keyboard(language))
            return False

        logger.info(f"Пользователь {user_id} подписан.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки для пользователя {user_id}: {str(e)}")
        return False
