from ..internals.database import get_cursor, get_conn

class DefaultCategory:
    def __init__(self, id: int, pure_name: str, display_name: str):
        self.id = id
        self.pure_name = pure_name
        self.display_name = display_name

def get_default_categories():
    with get_cursor() as cursor:
        query = 'SELECT id, pure_name, display_name FROM default_category'
        cursor.execute(query)
        default_categories = []
        for row in cursor.fetchall():
            default_category = DefaultCategory(row['id'], row['pure_name'], row['display_name'])
            default_categories.append(default_category)
        return default_categories

def get_default_categories_for_user(user_id: int, server_id: int):
    with get_cursor() as cursor:
        query = '''
            SELECT id, pure_name, display_name
            FROM default_category
            WHERE id NOT IN (
                SELECT * FROM default_category_opt_out WHERE user_id = %s AND server_id = %s
            )
        '''
        cursor.execute(query, (user_id, server_id,))
        default_categories = []
        for row in cursor.fetchall():
            default_category = DefaultCategory(row['id'], row['pure_name'], row['display_name'])
            default_categories.append(default_category)
        return default_categories

def get_default_category_id_map_for_user(user_id: int, server_id: int) -> dict:
    id_map = {}
    categories = get_default_categories_for_user(user_id, server_id)
    for category in categories:
        id_map[category.id] = category
    return id_map

def get_category_by_name(user_id: int, server_id: int, name: str):
    name = purify_name(name)
    with get_cursor() as cursor:
        query = 'SELECT id, display_name FROM default_category WHERE pure_name = %s'
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        if result is None:
            return None
        return DefaultCategory(result['id'], name, result['display_name'])

def is_category_being_used_by_activity(user_id: int, server_id: int, category_id: int):
    with get_cursor() as cursor:
        query = 'SELECT 1 FROM activity WHERE user_id = %s AND server_id = %s AND default_category_id = %s'
        cursor.execute(query, (user_id, server_id, category_id,))
        return cursor.fetchone() is not None

def is_default_category_name(name: str):
    with get_cursor() as cursor:
        query = 'SELECT 1 FROM default_category WHERE pure_name = %s'
        cursor.execute(query, (purify_name(name),))
        return cursor.fetchone() is not None

def opt_out_of_default_category(user_id: int, server_id: int, category_id: int):
    with get_conn() as conn:
        update_query = 'UPDATE activity SET default_category_id = NULL WHERE default_category_id = %s'
        insert_query = 'INSERT INTO default_category_opt_out (user_id, server_id, default_category_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING'
        cursor = conn.cursor()
        cursor.execute(update_query, (category_id,))
        cursor.execute(insert_query, (user_id, server_id, category_id,))
        cursor.commit()
        cursor.close()
