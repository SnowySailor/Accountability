import asyncio
import discord
import datetime
from discord.ext import commands
from src.utils.logger import logtofile
import src.lib.user as user_lib
import src.lib.wk_api as wk_api
from src.utils.utils import get_config
import traceback
import pytz

running = False
pending_review_disappointed_threshold = 25

async def do_daily_summary(bot: commands.Bot) -> None:
    global running
    if running:
        return

    try:
        running = True
        await asyncio.sleep(get_seconds_until_next_day_pacific_time())
        while True:
            users = user_lib.get_users_with_api_tokens()
            data = {}
            for user in users:
                reviews = wk_api.get_count_of_reviews_completed_yesterday(user.token)
                lessons = wk_api.get_lessons_completed_yesterday(user.token)
                pending_reviews = wk_api.get_count_of_reviews_available_before_end_of_yesterday(user.token)
                data[user.id] = {
                    'reviews': reviews,
                    'lessons': len(lessons),
                    'pending_reviews': pending_reviews
                }
            await send_daily_summary_message(data, bot)
            await asyncio.sleep(get_seconds_until_next_day_pacific_time())
    except:
        s = traceback.format_exc()
        content = f'Ignoring exception\n{s}'
        logtofile(content, 'error')
        running = False
        await do_daily_summary(bot)

async def send_daily_summary_message(data: dict, bot: commands.Bot) -> None:
    user_name = bot.user.name
    icon_url = bot.user.avatar_url
    channel = bot.get_channel(int(get_config('channel_id')))
    embed = discord.Embed(title=f'Daily WaniKani Summary', color=0xFF5733)

    message = ''
    disappointed_in_users = []
    for user_id, wk_data in data.items():
        user = channel.guild.get_member(user_id)
        lessons = wk_data['lessons']
        reviews = wk_data['reviews']
        pending_reviews = wk_data['pending_reviews']
        if pending_reviews >= pending_review_disappointed_threshold:
            disappointed_in_users.append(user.mention)
        if pending_reviews == 0:
            pending_reviews = 'no'
        message = f'Completed {lessons} lessons and {reviews} reviews\nHas {pending_reviews} available reviews'
        embed.add_field(name=user.display_name, value=message, inline=False)
    await channel.send(embed=embed)

    if len(disappointed_in_users) > 0:
        message = ' '.join(disappointed_in_users)
        message += f' you had at least {pending_review_disappointed_threshold} reviews remaining at the end of the day\n'
        message += 'https://tenor.com/view/anime-k-on-disappoint-disappointed-gif-6051447'
        await channel.send(message)

def get_seconds_until_next_day_pacific_time():
    day_delta = datetime.timedelta(days=1)
    now = datetime.datetime.now(pytz.timezone('America/Los_Angeles'))
    next_day = (now + day_delta).replace(microsecond=0, second=0, minute=1, hour=0)
    wait_seconds = (next_day - now).seconds
    return wait_seconds
