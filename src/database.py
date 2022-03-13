import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from utils import get_config

pool = None

def init_db():
    global pool
    try:
        pool = psycopg2.pool.ThreadedConnectionPool(1, 2000,
            host = get_config('database', 'host'),
            dbname = get_config('database', 'database'),
            user = get_config('database', 'user'),
            password = get_config('database', 'password'),
            port = get_config('database', 'host', default=5432),
            cursor_factory = RealDictCursor
        )
    except Exception as error:
        print("Failed to connect to the database: ", error)

@contextmanager
def get_conn(key: str = None):
    try:
        with pool.getconn(key) as conn:
            conn.autocommit = False
            yield conn
    except:
        raise
    finally:
        pool.putconn(conn, key)

@contextmanager
def get_cursor(key: str = None):
    try:
        with pool.getconn(key) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                yield cur
    except:
        raise
    finally:
        pool.putconn(conn, key)
