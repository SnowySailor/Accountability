import datetime

from ..internals.database import get_cursor

class Category:
    def __init__(self, id: int, user_id: int, server_id: int, pure_name: str, display_name: str, created_at: datetime.datetime):
        self.id = id
        self.user_id = user_id
        self.server_id = server_id
        self.pure_name = pure_name
        self.display_name = display_name
        self.created_at = created_at

def get_categories_for_user(user_id: int, server_id: int):
    categories = []
    with get_cursor() as cursor:
        query = 'SELECT id, pure_name, display_name, created_at FROM category WHERE user_id = %s AND server_id = %s'
        cursor.execute(query, (user_id, server_id,))
        for row in cursor.fetchall():
            category = Category(row['id'], user_id, server_id, row['pure_name'], row['display_name'], row['created_at'])
            categories.append(category)
        return categories

def get_category_by_name(user_id: int, server_id: int, name: str):
    name = purify_name(name)
    with get_cursor() as cursor:
        query = '''
            SELECT id, display_name, created_at
            FROM category
            WHERE user_id = %s AND server_id = %s AND pure_name = %s
        '''
        cursor.execute(query, (user_id, server_id, name,))
        result = cursor.fetchone()
        if result is None:
            return None
        return Category(result['id'], user_id, server_id, name, result['display_name'], result['created_at'])

def create_category_for_user(user_id: int, server_id: int, name: str):
    pure_name = purify_name(name)
    with get_cursor() as cursor:
        query = 'INSERT INTO category (user_id, server_id, pure_name, display_name) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING RETURNING id'
        cursor.execute(query, (user_id, server_id, pure_name, name,))
        return cursor.fetchone()

def update_category_name(category_id: int, new_name: str):
    pure_name = purify_name(new_name)
    with get_cursor() as cursor:
        query = 'UPDATE category SET pure_name = %s, display_name = %s WHERE id = %s'
        cursor.execute(query, (pure_name, new_name, category_id,))

def purify_name(name):
    return name.lower().strip()
