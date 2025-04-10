import logging
from src.services.analytics_creating_target import analytics_creating_target
from src.bot.bot_messages import MESSAGES

logger = logging.getLogger(__name__)


async def limit_check(limit, language, message, user_id, user_name):
    try:
        if limit is None:
            logger.error(f"Лимит для пользователя не найден.")
            return False

        if limit <= 0:
            if language:
                await message.ansver(MESSAGES["get_user_limit"][language])
            else:
                await message.ansver(MESSAGES["start"])
            await analytics_creating_target(user_id, user_name, target_start_id=10340, value=None, unit=None)
            return False

        return True
    except Exception as e:
        logger.error(f"Ошибка при проверке лимита: {str(e)}")
        await message.reply("Произошла ошибка при проверке лимита. Попробуйте позже.")
        return False
