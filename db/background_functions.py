import os
from db.database_connection import get_db_connection
import asyncio
from src.bot.bot_messages import MESSAGES
from aiogram import Bot
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta
import logging
from src.keyboards.check_subscriptions_keyboard import check_subscriptions_keyboard
from src.services.subscription_verification import check_subscription
from src.keyboards.reminder_keyboard import get_reminder_keyboard


logger = logging.getLogger(__name__)


async def send_reminder_work(bot):
    try:
        logger.info("Начало отправки напоминаний для пользователей с обучением.")
        time_24_hours_ago = datetime.now() - timedelta(hours=24)

        with get_db_connection() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:

                cursor.execute('''
                    SELECT users.id, users.user_id, users.created_at, users.language, training.status, training.reminder_sent
                    FROM users
                    LEFT JOIN training ON users.user_id = training.user_id
                    WHERE training.status = 0
                    AND training.reminder_sent = 0
                    AND users.created_at < %s
                ''', (time_24_hours_ago,))

                rows = cursor.fetchall()
                logger.info(f"Найдено {len(rows)} пользователей с непройденным обучением для отправки напоминаний.")

                for row in rows:
                    training_id, user_id, created_at, language, status, reminder_sent = row
                    message_text = MESSAGES['send_reminder_training'][language]

                    await bot.send_message(user_id, message_text, parse_mode="MarkdownV2")
                    logger.info(f"Отправлено напоминание пользователю {user_id} с текстом: {message_text}")

                    cursor.execute('''
                        UPDATE training
                        SET reminder_sent = 1
                        WHERE user_id = %s
                    ''', (user_id,))
                    connection.commit()
                    logger.info(f"Флаг reminder_sent обновлен для пользователя {user_id}.")

                for hours, column_name in [(24, 'reminder_24_sent'), (72, 'reminder_72_sent'),
                                           (168, 'reminder_168_sent')]:
                    time_threshold = datetime.now() - timedelta(hours=hours)

                    cursor.execute(f'''
                        SELECT users.id, users.user_id, users.language, training.{column_name},
                        CASE
                            WHEN EXISTS (SELECT 1 FROM user_history WHERE user_history.user_id = users.user_id)
                            THEN (SELECT MAX(user_history.created_at) FROM user_history WHERE user_history.user_id = users.user_id)
                            ELSE training.completed_at
                        END AS last_interaction
                        FROM users
                        LEFT JOIN training ON users.user_id = training.user_id
                        WHERE training.status = 1
                        AND training.{column_name} = 0
                        AND (
                            CASE
                                WHEN EXISTS (SELECT 1 FROM user_history WHERE user_history.user_id = users.user_id)
                                THEN (SELECT MAX(user_history.created_at) FROM user_history WHERE user_history.user_id = users.user_id)
                                ELSE training.completed_at
                            END
                        ) < %s
                        GROUP BY users.id, training.{column_name}
                    ''', (time_threshold,))

                    rows = cursor.fetchall()
                    logger.info(
                        f"Найдено {len(rows)} пользователей с завершенным обучением для отправки напоминаний на {hours} часов.")

                    for row in rows:
                        training_id, user_id, language, _, last_interaction = row
                        message_key = f'send_reminder_{hours}h'
                        message_text = MESSAGES[message_key][language]

                        if hours == 72:
                            reminder_keyboard = get_reminder_keyboard(language)
                            await bot.send_message(user_id, message_text, reply_markup=reminder_keyboard)
                        else:
                            await bot.send_message(user_id, message_text)
                        logger.info(f"Отправлено напоминание пользователю {user_id} с текстом: {message_text}")

                        cursor.execute(f'UPDATE training SET {column_name} = 1 WHERE user_id = %s', (user_id,))
                        connection.commit()
                        logger.info(f"Флаг {column_name} обновлен для пользователя {user_id}.")

            connection.commit()
    except Exception as e:
        logger.error(f"Ошибка в обработке пользователей: {str(e)}")


async def send_subscription_reminder(bot):
    try:
        logger.info("Начало отправки напоминаний о подписке.")

        time_24_hours_ago = datetime.now() - timedelta(hours=24)
        time_30_minutes_ago = datetime.now() - timedelta(minutes=30)

        with get_db_connection() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:

                cursor.execute('''
                    SELECT u.user_id, u.language, t.completed_at, 
                           t.reminder_24_sent_subscription, t.reminder_168_sent_subscription, 
                           (SELECT MAX(created_at) FROM user_history WHERE user_history.user_id = u.user_id) AS last_interaction
                    FROM users u
                    JOIN training t ON u.user_id = t.user_id
                    WHERE t.status = 1  -- Обучение завершено
                      AND t.completed_at IS NOT NULL
                      AND (t.reminder_24_sent_subscription = 0)
                ''')

                rows = cursor.fetchall()
                logger.info(f"Найдено {len(rows)} пользователей для отправки напоминаний о подписке.")

                for row in rows:
                    user_id, language, completed_at, reminder_24_sent, reminder_168_sent, last_interaction = row

                    if last_interaction:
                        last_interaction_dt = last_interaction  # В PostgreSQL timestamp уже в правильном формате
                        if last_interaction_dt > time_30_minutes_ago:
                            logger.info(
                                f"Пропуск отправки напоминания для пользователя {user_id}, так как последнее взаимодействие было недавно.")
                            continue

                    completed_at_datetime = completed_at  # В PostgreSQL timestamp уже правильный

                    is_subscribed = await check_subscription(user_id, bot)

                    if not is_subscribed:
                        if not reminder_24_sent and completed_at_datetime < time_24_hours_ago:
                            await bot.send_message(
                                user_id,
                                MESSAGES['send_subscription_reminder_24'][language] + os.getenv('CHANNEL_LINK'),
                                reply_markup=check_subscriptions_keyboard(language),
                            )
                            cursor.execute(
                                'UPDATE training SET reminder_24_sent_subscription = 1 WHERE user_id = %s', (user_id,)
                            )
                            logger.info(f"Отправлено 24-часовое напоминание о подписке пользователю {user_id}.")

                    connection.commit()

    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания о подписке: {str(e)}")


async def start_background_tasks(bot: Bot):
    """Запуск фоновой задачи для отправки напоминаний раз в 24 часа"""
    try:
        logger.info("Запуск фоновой задачи для отправки напоминаний.")
        while True:
            await send_reminder_work(bot)
            await send_subscription_reminder(bot)
            logger.info("Фоновые задачи выполнены, ожидаем следующий запуск.")
            await asyncio.sleep(86400)
    except Exception as e:
        logger.error(f"Ошибка при обработке фоновой задачи: {str(e)}")
