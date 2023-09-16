import redis
from os import getenv
import datetime
import pickle

from ..utils.utils import get_config

pool = None

def init_redis():
    global pool
    pool = redis.ConnectionPool(
        host = get_config('redis', 'host'),
        port = get_config('redis', 'port', default = 6379)
    )
    return pool

def try_init_redis(max_retries=7, delay=300):  
    for attempt in range(max_retries):
        try:
            init_db()
            print("Redis initialized successfully!")
            return
        except Exception as e:
            print(f"Failed to initialize the Redis on attempt {attempt + 1}: {e}")
            if attempt + 1 < max_retries:
                print(f"Waiting for {delay} seconds before retrying...")
                time.sleep(delay)
            else:
                print("Max retries reached. Giving up.")
                break

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
