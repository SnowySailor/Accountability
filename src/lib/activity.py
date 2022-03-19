import datetime
import pytz

from ..internals.database import get_cursor
from .user import get_current_time_for_user, get_timezone_for_user
import src.lib.category as category
import src.lib.default_category as default_category

class Activity:
    def __init__(
        self,
        id: int,
        user_id: int,
        server_id: int,
        description: str,
        category_id: int,
        default_category_id: int,
        created_at: datetime.datetime
    ):
        self.id = id
        self.user_id = user_id
        self.server_id = server_id
        self.description = description
        self.category_id = category_id
        self.default_category_id = default_category_id
        self.created_at = created_at

def log_activity_for_user(user_id: int, server_id: int, description: str, category_id: int = None, default_category_id: int = None) -> None:
    with get_cursor() as cursor:
        query = 'INSERT INTO activity (user_id, server_id, description, category_id, default_category_id) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(query, (user_id, server_id, description, category_id, default_category_id,))

def group_activities_by_category(user_id: int, server_id: int, activities: list) -> dict:
    if len(activities) == 0:
        return {}

    categories = category.get_category_id_map_for_user(user_id, server_id)
    default_categories = default_category.get_default_category_id_map_for_user(user_id, server_id)

    activity_dict = {}
    for activity in activities:
        key = None
        if activity.category_id is not None:
            key = categories[activity.category_id].display_name
        elif activity.default_category_id is not None:
            key = default_categories[activity.default_category_id].display_name

        if key not in activity_dict:
            activity_dict[key] = []
        activity_dict[key].append(activity)

    for cat, activity_list in activity_dict.items():
        activity_dict[cat] = list(sorted(activity_list, key=lambda x: x.created_at))

    no_category_activities = activity_dict[None]
    del activity_dict[None]
    activity_dict = dict(sorted(activity_dict.items()))
    activity_dict[None] = no_category_activities
    return activity_dict

def get_activities_for_user_for_today(user_id: int, server_id: int) -> list:
    activities = []

    user_time = get_current_time_for_user(user_id)
    user_timezone = pytz.timezone(get_timezone_for_user(user_id))
    day_beginning = datetime.datetime(user_time.year, user_time.month, user_time.day)
    day_end = datetime.datetime(user_time.year, user_time.month, user_time.day) + datetime.timedelta(days=1)

    new_timezone = pytz.timezone('UTC')
    search_start = str(user_timezone.localize(day_beginning).astimezone(new_timezone))
    search_end = str(user_timezone.localize(day_end).astimezone(new_timezone))

    with get_cursor() as cursor:
        query = '''
            SELECT id, description, created_at, category_id, default_category_id
            FROM activity
            WHERE user_id = %s
                AND server_id = %s
                AND created_at >= %s::timestamp
                AND created_at < %s::timestamp
        '''
        cursor.execute(query, (user_id, server_id, search_start, search_end,))
        for row in cursor.fetchall():
            activity = Activity(row['id'], user_id, server_id, row['description'], row['category_id'], row['default_category_id'], row['created_at'])
            activities.append(activity)
    return group_activities_by_category(user_id, server_id, activities)

def remove_activity(activity_id: int) -> None:
    with get_cursor() as cursor:
        query = 'DELETE FROM activity WHERE id = %s'
        cursor.execute(query, (activity_id,))

def update_activity_description(activity_id, new_description) -> None:
    with get_cursor() as cursor:
        query = 'UPDATE activity SET description = %s WHERE id = %s'
        cursor.execute(query, (new_description, activity_id,))
