import datetime

from ..internals.database import get_cursor, get_conn
from src.utils.utils import purify_category_name

class Category:
    def __init__(self, id: int, user_id: int, channel_id: int, pure_name: str, display_name: str, created_at: datetime.datetime):
        self.id = id
        self.user_id = user_id
        self.channel_id = channel_id
        self.pure_name = pure_name
        self.display_name = display_name
        self.created_at = created_at

def get_categories_for_user(user_id: int, channel_id: int) -> list:
    categories = []
    with get_cursor() as cursor:
        query = 'SELECT id, pure_name, display_name, created_at FROM category WHERE user_id = %s AND channel_id = %s'
        cursor.execute(query, (user_id, channel_id,))
        for row in cursor.fetchall():
            category = Category(row['id'], user_id, channel_id, row['pure_name'], row['display_name'], row['created_at'])
            categories.append(category)
        return categories

def get_category_id_map_for_user(user_id: int, channel_id: int) -> dict:
    id_map = {}
    categories = get_categories_for_user(user_id, channel_id)
    for category in categories:
        id_map[category.id] = category
    return id_map

def get_category_by_name(user_id: int, channel_id: int, name: str):
    name = purify_category_name(name)
    with get_cursor() as cursor:
        query = '''
            SELECT id, display_name, created_at
            FROM category
            WHERE user_id = %s AND channel_id = %s AND pure_name = %s
        '''
        cursor.execute(query, (user_id, channel_id, name,))
        result = cursor.fetchone()
        if result is None:
            return None
        return Category(result['id'], user_id, channel_id, name, result['display_name'], result['created_at'])

def create_category_for_user(user_id: int, channel_id: int, name: str):
    pure_name = purify_category_name(name)
    with get_cursor() as cursor:
        query = 'INSERT INTO category (user_id, channel_id, pure_name, display_name) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING RETURNING id'
        cursor.execute(query, (user_id, channel_id, pure_name, name,))
        return cursor.fetchone()

def update_category_name(category_id: int, new_name: str) -> None:
    pure_name = purify_category_name(new_name)
    with get_cursor() as cursor:
        query = 'UPDATE category SET pure_name = %s, display_name = %s WHERE id = %s'
        cursor.execute(query, (pure_name, new_name, category_id,))

def is_category_being_used_by_activity(user_id: int, channel_id: int, category_id: int) -> bool:
    with get_cursor() as cursor:
        query = 'SELECT 1 FROM activity WHERE user_id = %s AND channel_id = %s AND category_id = %s'
        cursor.execute(query, (user_id, channel_id, category_id,))
        return cursor.fetchone() is not None

def delete_category(category_id: int) -> None:
    # Need to do this transactionally
    with get_conn() as conn:
        update_query = 'UPDATE activity SET category_id = NULL WHERE category_id = %s'
        delete_query = 'DELETE FROM category WHERE id = %s'
        cursor = conn.cursor()
        cursor.execute(update_query, (category_id,))
        cursor.execute(delete_query, (category_id,))
        conn.commit()
        cursor.close()
