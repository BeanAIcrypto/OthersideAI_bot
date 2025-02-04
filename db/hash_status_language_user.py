import json
import sqlite3
from db.dbworker import get_db_connection, logger
import logging
import os


logger = logging.getLogger(__name__)

USER_DATA_FILE = os.getenv('USER_DATA_FILE')

def create_hash():
    user_data = {}

    try:
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT users.user_id, users.language, training.status
                FROM users
                LEFT JOIN training ON users.user_id = training.user_id
            ''')
            rows = cursor.fetchall()
            for row in rows:
                user_id = str(row[0])
                language = row[1]
                user_data[user_id] = {
                    'language': language
                }

            with open(USER_DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(user_data, file, ensure_ascii=False, indent=4)
                logger.info(f"Данные пользователей успешно сохранены в {USER_DATA_FILE}.")

    except IOError as e:
        logger.error(f"Ошибка при сохранении данных пользователей в файл: {str(e)}")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при загрузке данных пользователей из базы данных: {str(e)}")
    except Exception as e:
        logger.error(e)

