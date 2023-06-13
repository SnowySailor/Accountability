# Accountability

Discord bot that makes use of the WaniKani API to alert users of important things:
1. When criticals come available for a user
1. When a user makes it to the next WaniKani level
1. When a user has 25+ reviews left 1 hour before the end of their day
    * Shames user if the day ends with more than 25 reviews remaining
1. When a user's day ends, a report of completed lessons and reviews is given

## Running

1. Create a `config.json` file in the `./config` directory based on the example
1. Create a `.env.postgres` file in the `./config` directory based on the example
1. Run `docker-compose up` to start the bot
