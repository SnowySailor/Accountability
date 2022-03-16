"""
add category to activity
"""

from yoyo import step

__depends__ = {'20220316_01_7dFlX-add-categories'}

steps = [
    step("""
        ALTER TABLE activity ADD COLUMN category_id INT NULL REFERENCES category(id);
        ALTER TABLE activity ADD COLUMN default_category_id INT NULL REFERENCES default_category(id);
        CREATE INDEX ON activity (category_id);
        CREATE INDEX ON activity (default_category_id);
        CREATE INDEX ON activity (user_id, server_id, category_id) WHERE category_id IS NOT NULL;
        CREATE INDEX ON activity (user_id, server_id, default_category_id) WHERE default_category_id IS NOT NULL;
    """)
]
