import asyncio
import discord
import aiohttp
from discord.ext import commands
import src.lib.user as user_lib
import src.lib.wk_api as wk_api
from src.utils.utils import get_config
from src.utils.time import get_seconds_until_next_hour
from src.internals.accountability_task import AccountabilityTask

class DailySummary(AccountabilityTask):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.type = 'daily_summary'

    async def looping_task(self) -> None:
        await asyncio.sleep(get_seconds_until_next_hour())
        users = user_lib.get_users_with_api_tokens()
        data = {}
        for user in users:
            try:
                if await wk_api.is_user_on_vacation_mode(user.token):
                    continue

                if user_lib.is_midnight_in_users_timezone(user.id):
                    reviews = await wk_api.get_count_of_assignments_updated_yesterday(user.token, user.timezone)
                    lessons = await wk_api.get_lessons_completed_yesterday(user.token, user.timezone)
                    pending_reviews = await wk_api.get_count_of_reviews_available_before_end_of_yesterday(user.token, user.timezone)
                    data[user.id] = {
                        'reviews': reviews,
                        'lessons': len(lessons),
                        'pending_reviews': pending_reviews
                    }
            except aiohttp.ClientResponseError as e:
                if e.code == 403:
                    await self.bot.complain_about_expired_key(user.id)
                    continue
        await self.send_daily_summary_message(data)

    async def send_daily_summary_message(self, data: dict) -> None:
        if len(data) == 0:
            return

        user_name = self.bot.user.name
        channel = self.bot.get_channel(int(get_config('channel_id')))
        embed = discord.Embed(title=f'Daily WaniKani Summary', color=0xFF5733)

        message = ''
        disappointed_in_users = []
        for user_id, wk_data in data.items():
            user = channel.guild.get_member(user_id)
            lessons = wk_data['lessons']
            reviews = wk_data['reviews']
            pending_reviews = wk_data['pending_reviews']
            if pending_reviews >= get_config('pending_review_disappointed_threshold'):
                disappointed_in_users.append(user.mention)
            if pending_reviews == 0:
                pending_reviews = 'no'

            reviews_text = '0'
            if reviews > 0:
                reviews_text = f'(at least) {reviews}'
            message = f'Completed {lessons} lessons and {reviews_text} reviews\nHas {pending_reviews} available reviews'

            embed.add_field(name=user.display_name, value=message, inline=False)
        await channel.send(embed=embed)

        if len(disappointed_in_users) > 0:
            pending_review_disappointed_threshold = get_config('pending_review_disappointed_threshold')
            message = ' '.join(disappointed_in_users)
            message += f' you had at least {pending_review_disappointed_threshold} reviews remaining at the end of the day\n'
            message += 'https://tenor.com/view/anime-k-on-disappoint-disappointed-gif-6051447'
            await channel.send(message)
