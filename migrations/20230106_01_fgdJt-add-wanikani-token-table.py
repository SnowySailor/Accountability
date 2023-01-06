"""
add wanikani token table
"""

from yoyo import step

__depends__ = {'20220316_03_MInjV-create-default-categories'}

steps = [
    step("""
        CREATE TABLE user_wanikani_token (
            id serial NOT NULL PRIMARY KEY,
            user_id bigint NOT NULL,
            token varchar(255) NOT NULL,
            UNIQUE (user_id)
        );
    """)
]
