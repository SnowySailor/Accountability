import asyncio
from discord.ext import commands
import src.lib.user as user_lib
import src.lib.wk_api as wk_api
from src.utils.utils import get_config
from src.utils.time import get_seconds_until_next_hour
from src.internals.accountability_task import AccountabilityTask

class DailyReviewWarning(AccountabilityTask):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.type = 'daily_review_warning'

    async def looping_task(self) -> None:
        await asyncio.sleep(get_seconds_until_next_hour())
        users = user_lib.get_users_with_api_tokens()
        almost_overdue_users = []
        for user in users:
            if await wk_api.is_user_on_vacation_mode(user.token):
                continue

            if user_lib.is_11pm_in_users_timezone(user.id):
                reviews = await wk_api.get_number_of_reviews_available_now(user.token)
                if reviews >= get_config('pending_review_disappointed_threshold'):
                    almost_overdue_users.append(user.id)
        if len(almost_overdue_users) > 0:
            await self.send_almost_overdue_message(almost_overdue_users)

    async def send_almost_overdue_message(self, data: dict) -> None:
        if len(data) == 0:
            return

        channel = self.bot.get_channel(int(get_config('channel_id')))

        almost_overdue_users = []
        for user_id in data:
            user = channel.guild.get_member(user_id)
            almost_overdue_users.append(user.mention)

        pending_review_disappointed_threshold = get_config('pending_review_disappointed_threshold')
        message = ' '.join(almost_overdue_users)
        message += f' you have at least {pending_review_disappointed_threshold} reviews remaining with only 1 hour remaining until the end of the day'
        await channel.send(message)
