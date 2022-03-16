"""
add categories
"""

from yoyo import step

__depends__ = {'20220313_01_X6GxM-rename-activity-to-description'}

steps = [
    step("""
        CREATE TABLE category (
            id serial PRIMARY KEY,
            user_id bigint NOT NULL,
            server_id bigint NOT NULL,
            pure_name varchar(50) NOT NULL,
            display_name varchar(50) NOT NULL,
            created_at timestamp NOT NULL DEFAULT (now() at time zone 'utc'),
            UNIQUE (user_id, server_id, pure_name)
        );
    """)
]
