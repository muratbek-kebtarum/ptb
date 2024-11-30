import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import closing

# Настройки подключения к базе данных
DATABASE_URL = "postgresql://muratbek:tarum2000@localhost:5432/telegram_bot_db"


# Функция для создания таблицы
def create_table():
    """Создаёт таблицу user_data, если её ещё нет."""
    query = """
    CREATE TABLE IF NOT EXISTS user_data (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        data TEXT NOT NULL
    );
    """
    execute_query(query)


# Функция для добавления данных
def add_data(user_id, data):
    """Добавляет запись в таблицу."""
    query = "INSERT INTO user_data (user_id, data) VALUES (%s, %s)"
    execute_query(query, (user_id, data))


# Функция для получения данных
def get_data(user_id, record_id=None):
    """
    Возвращает записи из таблицы для указанного пользователя.
    Если указан record_id, возвращает одну запись.
    """
    if record_id:
        query = "SELECT id, data FROM user_data WHERE user_id = %s AND id = %s"
        return fetch_one(query, (user_id, record_id))
    else:
        query = "SELECT id, data FROM user_data WHERE user_id = %s"
        return fetch_all(query, (user_id,))


# Функция для обновления данных
def update_data(user_id, record_id, new_data):
    """Обновляет запись с указанным record_id для пользователя."""
    query = "UPDATE user_data SET data = %s WHERE id = %s AND user_id = %s"
    execute_query(query, (new_data, record_id, user_id))


# Функция для удаления данных
def delete_data(user_id, record_id):
    """Удаляет запись с указанным record_id для пользователя."""
    query = "DELETE FROM user_data WHERE id = %s AND user_id = %s"
    execute_query(query, (record_id, user_id))


# Общие функции для выполнения запросов
def execute_query(query, params=None):
    """Выполняет запрос без возврата данных (INSERT, UPDATE, DELETE)."""
    with closing(psycopg2.connect(DATABASE_URL)) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()


def fetch_one(query, params=None):
    """Выполняет запрос и возвращает одну запись."""
    with closing(psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetch_all(query, params=None):
    """Выполняет запрос и возвращает все записи."""
    with closing(psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
