import redis
from os import getenv
import datetime
import pickle
import time

from src.utils.logger import logtofile
from ..utils.utils import get_config

pool = None

def init_redis():
    global pool
    pool = redis.ConnectionPool(
        host = get_config('redis', 'host'),
        port = get_config('redis', 'port', default = 6379)
    )
    return pool

def try_init_redis(max_tries = 5, delay = 60):
    if max_tries <= 0:
        logtofile("Max retries reached. Giving up.", 'error')
        exit(1)

    try:
        init_redis()
    except Exception as e:
        logtofile(f"Failed to initialize Redis: {e}", 'warning')
        time.sleep(delay)
        try_init_redis(max_tries - 1, delay)

def get_pool():
    global pool
    return pool

def get_redis():
    return redis.Redis(connection_pool=pool)

def delete_keys(pattern):
    redis = get_redis()
    keys = redis.keys(pattern)
    if len(keys) > 0:
        redis.delete(*keys)

def delete_key_list(keys):
    conn = get_redis()
    for key in keys:
        conn.delete(key)

def remember(key, callback, ttl = None, reload = False):
    redis = get_redis()
    content = redis.get(key)
    if content is None or reload:
        content = callback()
        redis.set(key, serialize(content), ttl)
    else:
        content = deserialize(content)
    return content

async def remember_async(key, callback, ttl = None, reload = False):
    redis = get_redis()
    content = redis.get(key)
    if content is None or reload:
        content = await callback()
        redis.set(key, serialize(content), ttl)
    else:
        content = deserialize(content)
    return content

def serialize(data):
    return pickle.dumps(data)

def deserialize(data):
    return pickle.loads(data)
