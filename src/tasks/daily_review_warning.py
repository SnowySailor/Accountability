import asyncio
import discord
from discord.ext import commands
import src.lib.user as user_lib
import src.lib.wk_api as wk_api
from src.utils.utils import get_config
from src.utils.time import get_seconds_until_next_hour
from src.internals.accountability_task import AccountabilityTask

async def do_daily_review_warning(bot: commands.Bot) -> None:
    # don't start immediately; wait until next hour before checking stuff
    await asyncio.sleep(get_seconds_until_next_hour())
    task = AccountabilityTask('daily_review_warning', bot, looping_task)
    await task.start()

async def looping_task(bot: commands.Bot) -> None:
    users = user_lib.get_users_with_api_tokens()
    almost_overdue_users = []
    for user in users:
        if user_lib.is_11pm_in_users_timezone(user.id):
            reviews = wk_api.get_number_of_lessons_available_now(user.token)
            if reviews > get_config('pending_review_disappointed_threshold'):
                almost_overdue_users.append(user.id)
    if len(almost_overdue_users) > 0:
        await send_almost_overdue_message(almost_overdue_users, bot)
    await asyncio.sleep(get_seconds_until_next_hour())

async def send_almost_overdue_message(data: dict, bot: commands.Bot) -> None:
    if len(data) == 0:
        return

    channel = bot.get_channel(int(get_config('channel_id')))

    almost_overdue_users = []
    for user_id in data:
        user = channel.guild.get_member(user_id)
        almost_overdue_users.append(user.mention)

    pending_review_disappointed_threshold = get_config('pending_review_disappointed_threshold')
    message = ' '.join(almost_overdue_users)
    message += f' you have at least {pending_review_disappointed_threshold} reviews remaining with only 1 hour remaining until the end of the day'
    await channel.send(message)
