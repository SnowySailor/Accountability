import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from yoyo import read_migrations
from yoyo import get_backend
import time

from src.utils.logger import logtofile
from ..utils.utils import get_config

pool = None

def init_db():
    global pool
    pool = psycopg2.pool.ThreadedConnectionPool(1, 2000,
        host = get_config('database', 'host'),
        dbname = get_config('database', 'database'),
        user = get_config('database', 'user'),
        password = get_config('database', 'password'),
        port = get_config('database', 'port', default=5432),
        cursor_factory = RealDictCursor
    )

def try_init_db(max_tries = 5, delay = 60):
    if max_tries <= 0:
        logtofile("Max retries reached. Giving up.", 'error')
        exit(1)

    try:
        init_db()
    except Exception as e:
        logtofile(f"Failed to initialize the database: {e}", 'warning')
        time.sleep(delay)
        try_init_db(max_tries - 1, delay)

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

def run_migrations(max_tries = 5, delay = 60):
    if max_tries <= 0:
        logtofile("Max retries reached. Giving up.", 'error')
        exit(1)

    try:
        backend = get_backend('postgres://' + get_config('database', 'user') + ':' + get_config('database', 'password') + '@' + get_config('database', 'host') + ':' + str(get_config('database', 'port', default=5432)) + '/' + get_config('database', 'database'))
        migrations = read_migrations('./migrations')
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))
    except Exception as e:
        logtofile(f"Failed to run database migrations: {e}", 'warning')
        time.sleep(delay)
        run_migrations(max_tries - 1, delay)
