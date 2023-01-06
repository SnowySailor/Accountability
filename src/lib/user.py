import datetime
import pytz

from ..internals.database import get_cursor
from ..utils.utils import get_value

def get_current_time_for_user(user_id: int):
    timezone = get_timezone_for_user(user_id)
    return datetime.datetime.now(pytz.timezone(timezone))

def get_timezone_for_user(user_id: int):
    with get_cursor() as cursor:
        query = 'SELECT timezone FROM user_timezone WHERE user_id = %s'
        cursor.execute(query, (user_id,))
        return get_value(cursor.fetchone(), 'timezone', 'America/New_York')

def set_timezone_for_user(user_id: int, timezone: str):
    if timezone not in pytz.all_timezones_set:
        return False

    with get_cursor() as cursor:
        query = 'INSERT INTO user_timezone (user_id, timezone) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET timezone = %s WHERE EXCLUDED.user_id = %s'
        cursor.execute(query, (user_id, timezone, timezone, user_id,))
        return True

def set_wanikani_api_token_for_user(user_id: int, token: str):
    with get_cursor() as cursor:
        query = 'INSERT INTO user_wanikani_token (user_id, token) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET token = %s WHERE EXCLUDED.user_id = %s'
        cursor.execute(query, (user_id, token, token, user_id,))

def remove_wanikani_api_token_for_user(user_id: int):
    with get_cursor() as cursor:
        query = 'DELETE FROM user_wanikani_token WHERE user_id = %s'
        cursor.execute(query, (user_id,))

def get_users_with_api_tokens():
    with get_cursor() as cursor:
        query = 'SELECT user_id, token FROM user_wanikani_token'
        cursor.execute(query)
        return cursor.fetchall()
