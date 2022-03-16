"""
create default categories
"""

from yoyo import step

__depends__ = {'20220316_02_E6OYy-add-category-to-activity'}

steps = [
    step("""
        CREATE TABLE default_category (
            id serial NOT NULL PRIMARY KEY,
            pure_name varchar(50) NOT NULL,
            display_name varchar(50) NOT NULL
        );

        INSERT INTO default_category (pure_name, display_name) VALUES
            ('vocabulary', 'Vocabulary'),
            ('sentence mining', 'Sentence Mining'),
            ('reading', 'Reading'),
            ('speaking', 'Speaking'),
            ('listening', 'Listening');

        CREATE TABLE default_category_opt_out (
            id serial NOT NULL PRIMARY KEY,
            user_id bigint NOT NULL,
            server_id bigint NOT NULL,
            default_category_id int NOT NULL REFERENCES default_category(id),
            created_at timestamp NOT NULL DEFAULT (now() at time zone 'utc'),
            UNIQUE (user_id, server_id, default_category_id)
        );
    """)
]
