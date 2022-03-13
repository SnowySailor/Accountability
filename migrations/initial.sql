CREATE TABLE activity (
    user_id varchar NOT NULL,
    server_id varchar NOT NULL,
    activity varchar(2000) NULL,
    created_at timestamp NOT NULL DEFAULT (now() at time zone 'utc'),
    PRIMARY KEY (user_id, server_id),
);
CREATE INDEX ON activity (user_id, server_id, created_at);

CREATE TABLE user_timezone (
    user_id varchar PRIMARY KEY,
    timezone varchar NOT NULL
);
