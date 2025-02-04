import psycopg2
import json
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timedelta
from db.google_sheets import (
    append_row_to_google_sheet,
    get_google_sheets_service
)
from db.database_connection import get_db_connection


logger = logging.getLogger(__name__)

load_dotenv()
initial_limit = 6666667
USER_DATA_FILE = os.getenv('USER_DATA_FILE')


def load_user_data():
    try:
        if os.path.exists(USER_DATA_FILE) and os.path.getsize(USER_DATA_FILE) > 0:
            with open(USER_DATA_FILE, "r") as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из JSON: {e}")
        return {}

def save_user_data(data):
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в JSON: {e}")


def create_db():
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE,
                    username TEXT,
                    language TEXT DEFAULT 'None',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subscription_reminder_sent INTEGER DEFAULT 0
                )''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    question TEXT,
                    response TEXT,
                    dialog_score TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )''')

                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_limit (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    user_limit REAL DEFAULT {initial_limit},
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )''')

                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS training (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE, 
                    status INTEGER DEFAULT 1,
                    reminder_sent INTEGER DEFAULT 0,
                    reminder_24_sent INTEGER DEFAULT 0,
                    reminder_72_sent INTEGER DEFAULT 0,
                    reminder_168_sent INTEGER DEFAULT 0,
                    reminder_24_sent_subscription INTEGER DEFAULT 0,
                    completed_at TIMESTAMP,
                    last_message TEXT DEFAULT '0',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )''')

                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS user_keyboards (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        language TEXT DEFAULT '',               -- create_language_keyboard()
                        pay TEXT DEFAULT '',                    -- pay_keyboard(url)
                        training TEXT DEFAULT '',               -- create_training_keyboard(language)
                        continuation_training TEXT DEFAULT '',  -- create_continuation_training_keyboard(language)
                        final_training TEXT DEFAULT '',         -- create_final_training_keyboard(language)
                        all_updates TEXT DEFAULT '',            -- create_all_updates_training_keyboard(language)
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )''')

                connection.commit()
                logger.info("Таблицы успешно созданы в базе данных.")
    except psycopg2.Error as e:
        logger.error(f"Ошибка при создании таблиц в базе данных: {str(e)}")
        raise


def create_user(user_id, username):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
                user = cursor.fetchone()

                if user is None:
                    cursor.execute('INSERT INTO users (user_id, username) VALUES (%s, %s)', (user_id, username))
                    cursor.execute('INSERT INTO training (user_id) VALUES (%s)', (user_id,))
                    cursor.execute('INSERT INTO user_limit (user_id) VALUES (%s)', (user_id,))
                    cursor.execute('INSERT INTO user_keyboards (user_id) VALUES (%s)', (user_id,))
                    connection.commit()
                    logger.info(f"Пользователь {user_id} добавлен в базу данных.")
                else:
                    logger.info(f"Пользователь {user_id} уже существует в базе данных.")
    except psycopg2.Error as e:
        logger.error(f"Ошибка при создании пользователя в базе данных: {str(e)}")


def update_user_data_file(user_id, language, status):
    try:
        user_data = load_user_data()
        user_id_str = str(user_id)
        user_data[user_id_str] = {
            'language': language
        }
        save_user_data(user_data)
    except Exception as e:
        logger.error(e)


def get_user_language(user_id: int) -> str:
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT language FROM users WHERE user_id = %s', (user_id,))
                row = cursor.fetchone()
                return row[0] if row else None
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении языка пользователя из базы данных: {str(e)}")


def get_user_limit(user_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT user_limit, created_at FROM user_limit WHERE user_id = %s', (user_id,))
                user_data = cursor.fetchone()

                if user_data:
                    user_limit, last_update_time = user_data
                    last_update_time = last_update_time.replace(tzinfo=None)

                    if datetime.now() - last_update_time > timedelta(days=1):
                        cursor.execute('''
                            UPDATE user_limit 
                            SET user_limit = %s, created_at = CURRENT_TIMESTAMP 
                            WHERE user_id = %s
                        ''', (initial_limit, user_id))
                        connection.commit()
                        logger.info(f"Лимит пользователя {user_id} сброшен до {initial_limit}")
                        return initial_limit
                    else:
                        logger.info(f"Лимит пользователя {user_id} успешно получен: {user_limit}")
                        return user_limit
                else:
                    logger.info(f"Лимит для пользователя {user_id} не найден.")
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении данных пользователя из базы данных: {str(e)}")


def get_user_training(user_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT status FROM training WHERE user_id = %s', (user_id,))
                row = cursor.fetchone()
                if row is not None:
                    return row[0]
                else:
                    logger.info(f"Статус обучения не найден для пользователя с id {user_id}")
                    return None
    except psycopg2.Error as e:
        logger.error(f"Ошибка определения статуса обучения: {e}")


def get_user_training_last_message(user_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT last_message FROM training WHERE user_id = %s', (user_id,))
                row = cursor.fetchone()
                if row is not None:
                    return row[0]
                else:
                    logger.info(f"Сообщение обучения не найден для пользователя с id {user_id}")
                    return None
    except psycopg2.Error as e:
        logger.error(f"Ошибка определения сообщения обучения: {e}")


def update_user_training_status(user_id, status):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                if status == 1:
                    completed_at = datetime.now()
                    cursor.execute('''
                        UPDATE training
                        SET status = %s, completed_at = %s
                        WHERE user_id = %s
                    ''', (status, completed_at, user_id))
                else:
                    cursor.execute('''
                        UPDATE training
                        SET status = %s
                        WHERE user_id = %s
                    ''', (status, user_id))
                connection.commit()
                logger.info(f"Статус обучения пользователя {user_id} обновлен на {status}")
                user_data = load_user_data()
                user_id_str = str(user_id)
                if user_id_str in user_data:
                    user_data[user_id_str]['status'] = status
                else:
                    user_data[user_id_str] = {'language': 'None', 'status': status}
                save_user_data(user_data)
    except Exception as e:
        logger.error(f"Ошибка обновления статуса: {str(e)}")


def update_user_training_last_message(user_id, last_message):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT user_id FROM training WHERE user_id = %s', (user_id,))
                training_record = cursor.fetchone()
                if training_record:
                    cursor.execute(
                        'UPDATE training SET last_message = %s WHERE user_id = %s',
                        (last_message, user_id))
                    connection.commit()
                    logger.info(f"Поле last_message обновлено для пользователя с user_id {user_id}.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении поля last_message для пользователя с user_id {user_id}: {str(e)}")


def update_user_limit(user_id, limit):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT id FROM users WHERE user_id = %s', (user_id,))
                limit_id = cursor.fetchone()
                if limit_id:
                    cursor.execute('UPDATE user_limit SET user_limit = %s WHERE user_id = %s', (limit, user_id))
                    connection.commit()
                    logger.info(f"Лимит {limit} пользователя {user_id} успешно обновлён в базе данных.")
    except psycopg2.Error as e:
        logger.error(f"Ошибка при обновлении лимита пользователя в базе данных: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных в Google Sheets: {str(e)}")


def update_user_language(user_id, language):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT id FROM users WHERE user_id = %s', (user_id,))
                row = cursor.fetchone()

                cursor.execute('UPDATE users SET language = %s WHERE user_id = %s', (language, user_id))
                connection.commit()
                logger.info(f"Язык пользователя {user_id} успешно обновлён в базе данных.")

                user_data = load_user_data()
                user_id_str = str(user_id)
                user_data[user_id_str]['language'] = language
                save_user_data(user_data)
                logger.info("Язык пользователя обновлен в json файле")
    except psycopg2.Error as e:
        logger.error(f"Ошибка при обновлении языка пользователя в базе данных: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных в Google Sheets: {str(e)}")


def add_history_entry(user_id, question, response):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user_history (user_id, question, response) VALUES (%s, %s, %s) RETURNING id",
                    (user_id, question, response)
                )
                history_id = cursor.fetchone()[0]
                connection.commit()
                logger.info(f"Запись в историю для пользователя {user_id} успешно добавлена.")
                return history_id
    except psycopg2.Error as e:
        logger.error(f"Ошибка при добавлении записи в историю в базе данных: {str(e)}")


def get_user_history(user_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''SELECT question, response 
                        FROM user_history
                        WHERE user_id = %s 
                        ORDER BY id DESC
                        LIMIT 5''',
                    (user_id,)
                )
                history = cursor.fetchall()[::-1]
                logger.info(f"История для пользователя {user_id} успешно получена из базы данных.")
                return [{'question': row[0], 'response': row[1]} for row in history]
    except psycopg2.Error as e:
        logger.error(f"Ошибка при получении истории пользователя из базы данных: {str(e)}")
        return []


def update_dialog_score(rating, response_id):
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM user_history WHERE id = %s', (response_id,))
                updated_row = cursor.fetchone()

                cursor.execute('''
                    UPDATE user_history
                    SET dialog_score = %s
                    WHERE id = %s
                ''', (rating, response_id))

                connection.commit()
                logger.info(f"Оценка для записи {response_id} успешно обновлена в базе данных.")

                if rating == "👎":
                    row_data = list(updated_row)
                    service = get_google_sheets_service()
                    append_row_to_google_sheet(service, row_data, 'history')
    except psycopg2.Error as e:
        logger.error(f"Ошибка при обновлении оценки диалога в базе данных: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных в Google Sheets: {str(e)}")


def update_get_user_keyboard(user_id, name_keyboard, keyboard_id):
    ALLOWED_KEYBOARDS = [
        'language',
        'pay',
        'training',
        'continuation_training',
        'final_training',
        'all_updates'
    ]
    try:
        if name_keyboard not in ALLOWED_KEYBOARDS:
            logger.error(f"Некорректное имя клавиатуры: {name_keyboard}")
            return

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT {name_keyboard} FROM user_keyboards WHERE user_id = %s', (user_id,))
                row = cursor.fetchone()
                current_value = row[0] if row else ''
                update_value = f'{current_value},{keyboard_id}' if current_value else str(keyboard_id)

                cursor.execute(
                    f'UPDATE user_keyboards SET {name_keyboard} = %s WHERE user_id = %s',
                    (update_value, user_id)
                )
                connection.commit()
                logger.info(f"Клавиатура {name_keyboard} обновлена для пользователя {user_id} с ID {keyboard_id}.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении ID клавиатуры для пользователя {user_id}: {str(e)}")

def delete_user_keyboard(user_id, name_keyboard):
    ALLOWED_KEYBOARDS = [
        'language',
        'pay',
        'training',
        'continuation_training',
        'final_training',
        'all_updates'
    ]
    try:
        if name_keyboard not in ALLOWED_KEYBOARDS:
            logger.error(f"Некорректное имя клавиатуры: {name_keyboard}")
            return

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT {name_keyboard} FROM user_keyboards WHERE user_id = %s', (user_id,))
                row = cursor.fetchone()
                current_value = row[0] if row else None
                if not current_value:
                    return current_value
                cursor.execute(
                    f'UPDATE user_keyboards SET {name_keyboard} = %s WHERE user_id = %s',
                    ('', user_id)
                )
                connection.commit()
                logger.info(f"Ид клавиатуры {name_keyboard} удалены.")
                return current_value
    except Exception as e:
        logger.error(f"Ошибка при обновлении ID клавиатуры для пользователя {user_id}: {str(e)}")
