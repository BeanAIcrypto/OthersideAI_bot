from db.dbworker import delete_user_keyboard
import logging

logger = logging.getLogger(__name__)


async def remove_keyboards_from_messages(bot, user_id, name_keyboard):
    try:
        message = delete_user_keyboard(user_id, name_keyboard)

        if not message:
            logger.info(f'Нет сохраненных ID клавиатуры {name_keyboard} для пользователя {user_id}')
            return

        list_message = message.split(',')
        for message_id in list_message:
            if message_id.isdigit() and int(message_id) > 0:
                try:
                    await bot.edit_message_reply_markup(user_id, int(message_id), reply_markup=None)
                except Exception as e:
                    logger.warning(f'Не удалось удалить клавиатуру из сообщения {message_id}: {str(e)}')
            else:
                logger.warning(f'Неверный ID сообщения: {message_id}')
    except Exception as e:
        logger.error(f'Ошибка удаления клавиатур: {str(e)}')
