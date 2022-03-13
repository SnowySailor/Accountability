CREATE TABLE activity (
    id serial PRIMARY KEY,
    user_id bigint NOT NULL,
    server_id bigint NOT NULL,
    activity varchar(2000) NULL,
    created_at timestamp NOT NULL DEFAULT (now() at time zone 'utc')
);
CREATE INDEX ON activity (user_id, server_id, created_at);

CREATE TABLE user_timezone (
    user_id bigint PRIMARY KEY,
    timezone varchar NOT NULL
);
