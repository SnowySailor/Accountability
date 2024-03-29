import datetime
import pytz
from typing import Union

from ..internals.database import get_cursor
from ..utils.utils import get_value

class User:
    def __init__(
        self,
        id: int,
        token: str,
        timezone: Union[str, None]
    ):
        self.id = id
        self.token = token
        self.timezone = timezone

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
        query = 'SELECT user_id, token FROM user_wanikani_token uwt'
        cursor.execute(query)
        users = []
        for row in cursor.fetchall():
            users.append(User(row['user_id'], row['token'], get_timezone_for_user(row['user_id'])))
        return users

def get_wanikani_api_token(user_id: int) -> Union[str, None]:
    with get_cursor() as cursor:
        query = 'SELECT token FROM user_wanikani_token WHERE user_id = %s'
        cursor.execute(query, (user_id,))
        return get_value(cursor.fetchone(), 'token')

def is_midnight_in_users_timezone(user_id: int) -> bool:
    t = get_current_time_for_user(user_id)
    return t.hour == 0

def is_11pm_in_users_timezone(user_id: int) -> bool:
    t = get_current_time_for_user(user_id)
    return t.hour == 23
