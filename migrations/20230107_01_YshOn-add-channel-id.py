"""
Add channel id
"""

from yoyo import step

__depends__ = {'20230106_01_fgdJt-add-wanikani-token-table'}

steps = [
    step("""
        DROP INDEX activity_user_id_server_id_category_id_idx;
        DROP INDEX activity_user_id_server_id_created_at_idx;
        DROP INDEX activity_user_id_server_id_default_category_id_idx;
        ALTER TABLE activity ADD COLUMN channel_id BIGINT NOT NULL DEFAULT 953147358206640238;
        ALTER TABLE activity DROP COLUMN server_id;
        CREATE INDEX ON activity (user_id, channel_id, category_id) WHERE category_id IS NOT NULL;

        ALTER TABLE category DROP CONSTRAINT category_user_id_server_id_pure_name_key;
        ALTER TABLE category ADD COLUMN channel_id BIGINT NOT NULL DEFAULT 953147358206640238;
        ALTER TABLE category DROP COLUMN server_id;
        CREATE INDEX ON category (user_id, channel_id);

        ALTER TABLE default_category_opt_out DROP CONSTRAINT default_category_opt_out_user_id_server_id_default_category_key;
        ALTER TABLE default_category_opt_out ADD COLUMN channel_id BIGINT NOT NULL DEFAULT 953147358206640238;
        ALTER TABLE default_category_opt_out DROP COLUMN server_id;
        CREATE INDEX ON default_category_opt_out (user_id, channel_id, default_category_id);

        ALTER TABLE activity ALTER channel_id DROP DEFAULT;
        ALTER TABLE category ALTER channel_id DROP DEFAULT;
        ALTER TABLE default_category_opt_out ALTER channel_id DROP DEFAULT;
    """)
]
