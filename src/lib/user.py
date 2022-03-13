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
    if timezone not in pytz.all_timezones:
        return False

    with get_cursor() as cursor:
        query = 'INSERT INTO user_timezone (user_id, timezone) VALUES (%s, %s) ON CONFLICT DO UPDATE SET timezone = %s WHERE user_id = %s'
        cursor.execute(query, (user_id, timezone, timezone, user_id,))
