import datetime

from src.internals.database import get_cursor

class Goal:
    def __init__(
        self,
        id: int,
        user_id: int,
        server_id: int,
        category_id: int,
        default_category_id: int,
        target_hour: int,
        created_at: datetime.datetime
    ):
        self.id = id
        self.user_id = user_id
        self.server_id = server_id
        self.category_id = category_id
        self.default_category_id = default_category_id
        self.target_hour = target_hour
        self.created_at = created_at

def get_overdue_goals() -> list:
    overdue_goals = {}
    with get_cursor() as cursor:
        query = '''
            SELECT g.user_id, g.server_id, c.display_name as cname, dc.display_name as dcname
            FROM goal g
            LEFT JOIN category c ON g.category_id = c.id
            LEFT JOIN default_category dc ON g.default_category_id = dc.id
            WHERE
                EXTRACT(hour FROM (NOW() AT TIME ZONE (SELECT timezone FROM user_timezone WHERE user_id = g.user_id))) > g.alert_hour
                AND NOT EXISTS (
                    SELECT 1
                    FROM goal_ping gp
                    WHERE
                        gp.goal_id = g.id
                        AND
                        gp.created_at > (CURRENT_DATE::TIMESTAMP AT TIME ZONE (SELECT timezone FROM user_timezone WHERE user_id = g.user_id))
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM activity a
                    WHERE
                        a.user_id = g.user_id
                        AND
                        a.server_id = g.server_id
                        AND
                        a.created_at > (CURRENT_DATE::TIMESTAMP AT TIME ZONE (SELECT timezone FROM user_timezone WHERE user_id = g.user_id))
                )
        '''
        cursor.execute(query)
        for row in cursor.fetchall():
            key = (row['user_id'], row['server_id'])
            display_name = row['cname'] if row['cname'] is not None else row['dcname']
            if key not in overdue_goals:
                overdue_goals[key] = []
            overdue_goals[key].append(display_name)

    return overdue_goals

def log_goal_ping(user_id: int, server_id: int, goal_id: int) -> None:
    pass

def create_goal_for_user(user_id: int, server_id: int, category_id: int, default_category_id: int) -> int:
    pass

def delete_goal(goal_id: int) -> None:
    pass
