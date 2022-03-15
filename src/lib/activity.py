import datetime
import pytz

from ..internals.database import get_cursor
from .user import get_current_time_for_user, get_timezone_for_user

class Activity:
    def __init__(self, id: int, user_id: int, server_id: int, description: str, created_at: datetime.datetime):
        self.id = id
        self.user_id = user_id
        self.server_id = server_id
        self.description = description
        self.created_at = created_at

def log_activity_for_user(user_id: int, server_id: int, description: str):
    with get_cursor() as cursor:
        query = 'INSERT INTO activity (user_id, server_id, description) VALUES (%s, %s, %s)'
        cursor.execute(query, (user_id, server_id, description,))

def get_activities_for_user_for_today(user_id: int, server_id: int):
    activities = []

    user_time = get_current_time_for_user(user_id)
    user_timezone = pytz.timezone(get_timezone_for_user(user_id))
    day_beginning = datetime.datetime(user_time.year, user_time.month, user_time.day)
    day_end = datetime.datetime(user_time.year, user_time.month, user_time.day) + datetime.timedelta(days=1)

    new_timezone = pytz.timezone('UTC')
    search_start = str(user_timezone.localize(day_beginning).astimezone(new_timezone))
    search_end = str(user_timezone.localize(day_end).astimezone(new_timezone))

    with get_cursor() as cursor:
        query = 'SELECT id, description, created_at FROM activity WHERE user_id = %s AND server_id = %s AND created_at >= %s::timestamp AND created_at < %s::timestamp'
        cursor.execute(query, (user_id, server_id, search_start, search_end,))
        for row in cursor.fetchall():
            activity = Activity(row['id'], user_id, server_id, row['description'], row['created_at'])
            activities.append(activity)
    return activities

def remove_activity(activity_id: int):
    with get_cursor() as cursor:
        query = 'DELETE FROM activity WHERE id = %s'
        cursor.execute(query, (activity_id,))

def update_activity_description(activity_id, new_description):
    with get_cursor() as cursor:
        query = 'UPDATE activity SET description = %s WHERE id = %s'
        cursor.execute(query, (new_description, activity_id,))
