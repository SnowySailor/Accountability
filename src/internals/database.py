import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from yoyo import read_migrations
from yoyo import get_backend

from ..utils.utils import get_config

pool = None

def init_db():
    global pool
    try:
        pool = psycopg2.pool.ThreadedConnectionPool(1, 2000,
            host = get_config('database', 'host'),
            dbname = get_config('database', 'database'),
            user = get_config('database', 'user'),
            password = get_config('database', 'password'),
            port = get_config('database', 'port', default=5432),
            cursor_factory = RealDictCursor
        )
    except Exception as error:
        print("Failed to connect to the database: ", error)
        raise

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

def run_migrations():
    backend = get_backend('postgres://' + get_config('database', 'user') + ':' + get_config('database', 'password') + '@' + get_config('database', 'host') + ':' + str(get_config('database', 'port', default=5432)) + '/' + get_config('database', 'database'))
    migrations = read_migrations('./migrations')
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
