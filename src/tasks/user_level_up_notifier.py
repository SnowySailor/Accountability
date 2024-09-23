import asyncio
import requests
from discord.ext import commands
import src.lib.user as user_lib
import src.lib.wk_api as wk_api
from src.utils.utils import get_config, get_multi_level_value, get_value, parse_timestamp
from src.utils.time import get_seconds_until_next_hour, get_start_of_previous_hour_utc
from src.internals.accountability_task import AccountabilityTask

class UserLevelUpNotifier(AccountabilityTask):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.type = 'user_level_up_alert'

    async def looping_task(self) -> None:
        await asyncio.sleep(get_seconds_until_next_hour())
        users = user_lib.get_users_with_api_tokens()
        for user in users:
            try:
                progressions = await wk_api.get_user_level_progressions(user.token)
                for level in progressions['data']:
                    unlocked_timestamp_str = get_multi_level_value(level, 'data', 'unlocked_at', default = '1900-01-01T00:00:00.000000Z')
                    unlocked_timestamp = parse_timestamp(unlocked_timestamp_str)
                    if unlocked_timestamp > get_start_of_previous_hour_utc():
                        await self.notify_of_level_up(user.id, get_multi_level_value(level, 'data', 'level'))
                        break
            except requests.exceptions.RequestException as e:
                if e.response.status_code == 403:
                    continue

    async def notify_of_level_up(self, user_id: int, new_level: int) -> None:
        channel = self.bot.get_channel(int(get_config('channel_id')))
        await channel.send(f'<@{user_id}> made it to level {new_level}')
