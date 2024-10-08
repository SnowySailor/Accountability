import asyncio
from discord.ext import commands
import src.lib.user as user_lib
import src.lib.wk_api as wk_api
import aiohttp
from src.utils.utils import get_config, get_multi_level_value, get_value
from src.utils.time import get_seconds_until_next_hour
from src.internals.accountability_task import AccountabilityTask

class CriticalChecks(AccountabilityTask):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.type = 'critical_checks'

    async def looping_task(self) -> None:
        await asyncio.sleep(get_seconds_until_next_hour())
        users = user_lib.get_users_with_api_tokens()
        users_to_notify = []
        for user in users:
            try:
                assignments = await wk_api.get_new_assignments_this_hour(user.token)
                for assignment in assignments:
                    if get_multi_level_value(assignment, 'data', 'passed_at') is not None:
                        continue

                    if get_multi_level_value(assignment, 'data', 'srs_stage', default=5) > 4:
                        continue

                    if get_multi_level_value(assignment, 'data', 'subject_type') not in ['radical', 'kanji']:
                        continue

                    subject_id = get_multi_level_value(assignment, 'data', 'subject_id')
                    subject = await wk_api.get_subject(subject_id, user.token)
                    wk_user = await wk_api.get_user(user.token)
                    if get_value(subject, 'level') == get_value(wk_user, 'level'):
                        users_to_notify.append(user.id)
                        break
            except aiohttp.ClientResponseError as e:
                if e.code == 403:
                    await self.bot.complain_about_expired_key(user.id)
                    continue

        if len(users_to_notify) > 0:
            await self.notify_of_new_criticals(users_to_notify)

    async def notify_of_new_criticals(self, users_to_notify: list) -> None:
        channel = self.bot.get_channel(int(get_config('channel_id')))
        mentions_string = ''
        for user_id in users_to_notify:
            member = channel.guild.get_member(user_id)
            mentions_string += member.mention + ' '
        await channel.send(f'{mentions_string}you have criticals up for review')
