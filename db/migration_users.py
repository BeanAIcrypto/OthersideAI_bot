import os
import logging
import sqlite3

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Инициализация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения (если используете .env)
load_dotenv()

# Настройки подключения к PostgreSQL
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'mydb'),
    'user': os.getenv('DB_USER', 'myuser'),
    'password': os.getenv('DB_PASSWORD', 'mypassword'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Путь к SQLite-файлу (адаптируйте под свой docker-контейнер или локальную среду)
# SQLITE_DB_PATH = "/app/db/database.db"
SQLITE_DB_PATH = "database.db"

def get_sqlite_connection() -> sqlite3.Connection:
    """
    Подключение к SQLite.
    """
    try:
        return sqlite3.connect(SQLITE_DB_PATH)
    except sqlite3.Error as e:
        logger.error(f"Ошибка при подключении к SQLite: {str(e)}")
        raise

def get_postgres_connection() -> psycopg2.extensions.connection:
    """
    Подключение к PostgreSQL.
    """
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as error:
        logger.error(f"Ошибка операционного соединения с PostgreSQL: {error}")
        raise
    except psycopg2.DatabaseError as error:
        logger.error(f"Ошибка базы данных PostgreSQL: {error}")
        raise
    except Exception as error:
        logger.error(f"Неизвестная ошибка при подключении к PostgreSQL: {error}")
        raise

def table_exists_in_postgres(conn: psycopg2.extensions.connection, table_name: str) -> bool:
    """
    Проверяем, существует ли таблица table_name в PostgreSQL (public.schema).
    Возвращает True или False.
    """
    schema_and_table = f"public.{table_name}"
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT to_regclass(%s)""",
            (table_name,)
        )
        result = cursor.fetchone()
        return (result[0] is not None)  # None, если таблица отсутствует

def migrate_users(sqlite_conn: sqlite3.Connection, pg_conn: psycopg2.extensions.connection):
    """
    Перенос таблицы users из SQLite в PostgreSQL.
    """
    if not table_exists_in_postgres(pg_conn, 'users'):
        logger.info("Таблица users не существует в PostgreSQL. Пропускаем перенос.")
        return

    logger.info("Начинаем перенос таблицы users.")
    sqlite_cursor = sqlite_conn.cursor()

    # Извлекаем данные из SQLite
    sqlite_cursor.execute("""
        SELECT 
            user_id,                -- INTEGER
            username,               -- TEXT
            language,               -- TEXT
            created_at,             -- TIMESTAMP
            subscription_reminder_sent  -- INTEGER
        FROM users
    """)
    rows = sqlite_cursor.fetchall()
    logger.info(f"Найдено {len(rows)} записей в SQLite(users).")

    if not rows:
        return

    # Вставляем данные в PostgreSQL, используя ON CONFLICT (user_id) DO NOTHING,
    # так как в PostgreSQL user_id BIGINT UNIQUE (по условию).
    insert_query = """
        INSERT INTO users (
            user_id,
            username,
            language,
            created_at,
            subscription_reminder_sent
        )
        VALUES %s
        ON CONFLICT (user_id) DO NOTHING
    """

    with pg_conn.cursor() as cursor:
        execute_values(cursor, insert_query, rows)

    pg_conn.commit()
    logger.info("Таблица users успешно перенесена.")

def migrate_user_history(sqlite_conn: sqlite3.Connection, pg_conn: psycopg2.extensions.connection):
    """
    Перенос таблицы user_history из SQLite в PostgreSQL.
    """
    if not table_exists_in_postgres(pg_conn, 'user_history'):
        logger.info("Таблица user_history не существует в PostgreSQL. Пропускаем перенос.")
        return

    logger.info("Начинаем перенос таблицы user_history.")
    sqlite_cursor = sqlite_conn.cursor()

    # Извлекаем данные
    sqlite_cursor.execute("""
        SELECT
            user_id,        -- INTEGER (FK на users)
            question,       -- TEXT
            response,       -- TEXT
            dialog_score,   -- TEXT (или NULL)
            created_at      -- TIMESTAMP
        FROM user_history
    """)
    rows = sqlite_cursor.fetchall()
    logger.info(f"Найдено {len(rows)} записей в SQLite(user_history).")

    if not rows:
        return

    # Вставка без ON CONFLICT, так как id SERIAL PRIMARY KEY в Postgres
    # и нет уникального ограничения на user_id
    insert_query = """
        INSERT INTO user_history (
            user_id,
            question,
            response,
            dialog_score,
            created_at
        )
        VALUES %s
    """

    with pg_conn.cursor() as cursor:
        execute_values(cursor, insert_query, rows)

    pg_conn.commit()
    logger.info("Таблица user_history успешно перенесена.")

def migrate_user_limit(sqlite_conn: sqlite3.Connection, pg_conn: psycopg2.extensions.connection):
    """
    Перенос таблицы user_limit из SQLite в PostgreSQL.
    """
    if not table_exists_in_postgres(pg_conn, 'user_limit'):
        logger.info("Таблица user_limit не существует в PostgreSQL. Пропускаем перенос.")
        return

    logger.info("Начинаем перенос таблицы user_limit.")
    sqlite_cursor = sqlite_conn.cursor()

    # Извлекаем данные
    sqlite_cursor.execute("""
        SELECT
            user_id,       -- INTEGER
            user_limit,    -- REAL
            created_at     -- TIMESTAMP
        FROM user_limit
    """)
    rows = sqlite_cursor.fetchall()
    logger.info(f"Найдено {len(rows)} записей в SQLite(user_limit).")

    if not rows:
        return

    # Вставка данных без ON CONFLICT, если у user_limit нет уникального ключа
    insert_query = """
        INSERT INTO user_limit (
            user_id,
            user_limit,
            created_at
        )
        VALUES %s
    """

    with pg_conn.cursor() as cursor:
        execute_values(cursor, insert_query, rows)

    pg_conn.commit()
    logger.info("Таблица user_limit успешно перенесена.")

def migrate_training(sqlite_conn: sqlite3.Connection, pg_conn: psycopg2.extensions.connection):
    """
    Перенос таблицы training из SQLite в PostgreSQL.
    Учитываем, что user_id BIGINT UNIQUE в PostgreSQL.
    """
    if not table_exists_in_postgres(pg_conn, 'training'):
        logger.info("Таблица training не существует в PostgreSQL. Пропускаем перенос.")
        return

    logger.info("Начинаем перенос таблицы training.")
    sqlite_cursor = sqlite_conn.cursor()

    # Извлекаем данные
    sqlite_cursor.execute(f"""
        SELECT
            user_id,                  -- INTEGER UNIQUE
            status,                   -- INTEGER
            reminder_sent,            -- INTEGER
            reminder_24_sent,         -- INTEGER
            reminder_72_sent,         -- INTEGER
            reminder_168_sent,        -- INTEGER
            reminder_24_sent_subscription, -- INTEGER
            completed_at,             -- TIMESTAMP
            last_message              -- TEXT
        FROM training
    """)
    rows = sqlite_cursor.fetchall()
    logger.info(f"Найдено {len(rows)} записей в SQLite(training).")

    if not rows:
        return

    # Поскольку user_id в PostgreSQL уникален, используем ON CONFLICT (user_id) DO NOTHING.
    insert_query = """
        INSERT INTO training (
            user_id,
            status,
            reminder_sent,
            reminder_24_sent,
            reminder_72_sent,
            reminder_168_sent,
            reminder_24_sent_subscription,
            completed_at,
            last_message
        )
        VALUES %s
        ON CONFLICT (user_id) DO NOTHING
    """

    with pg_conn.cursor() as cursor:
        execute_values(cursor, insert_query, rows)

    pg_conn.commit()
    logger.info("Таблица training успешно перенесена.")

def migrate_user_keyboards(sqlite_conn: sqlite3.Connection, pg_conn: psycopg2.extensions.connection):
    """
    Перенос таблицы user_keyboards из SQLite в PostgreSQL.
    """
    if not table_exists_in_postgres(pg_conn, 'user_keyboards'):
        logger.info("Таблица user_keyboards не существует в PostgreSQL. Пропускаем перенос.")
        return

    logger.info("Начинаем перенос таблицы user_keyboards.")
    sqlite_cursor = sqlite_conn.cursor()

    # Извлекаем данные
    sqlite_cursor.execute("""
        SELECT
            user_id,               -- INTEGER
            language,             -- TEXT
            pay,                  -- TEXT
            training,             -- TEXT
            continuation_training,-- TEXT
            final_training,       -- TEXT
            all_updates           -- TEXT
        FROM user_keyboards
    """)
    rows = sqlite_cursor.fetchall()
    logger.info(f"Найдено {len(rows)} записей в SQLite(user_keyboards).")

    if not rows:
        return

    # Без ON CONFLICT, т.к. не указано уникальное поле в user_keyboards
    insert_query = """
        INSERT INTO user_keyboards (
            user_id,
            language,
            pay,
            training,
            continuation_training,
            final_training,
            all_updates
        )
        VALUES %s
    """

    with pg_conn.cursor() as cursor:
        execute_values(cursor, insert_query, rows)

    pg_conn.commit()
    logger.info("Таблица user_keyboards успешно перенесена.")

def mirgration_users():
    """
    Основная функция, где последовательно вызываем миграцию всех таблиц.
    Если какой-то таблицы нет в PostgreSQL, пропускаем её.
    """
    with get_sqlite_connection() as sqlite_conn, get_postgres_connection() as pg_conn:
        migrate_users(sqlite_conn, pg_conn)
        migrate_user_history(sqlite_conn, pg_conn)
        migrate_user_limit(sqlite_conn, pg_conn)
        migrate_training(sqlite_conn, pg_conn)
        migrate_user_keyboards(sqlite_conn, pg_conn)

        logger.info("Миграция всех таблиц завершена.")

if __name__ == "__main__":
    mirgration_users()
