import asyncio
import discord
import datetime
from discord.ext import commands
from src.utils.logger import logtofile
import src.lib.user as user_lib
import src.lib.wk_api as wk_api
from src.utils.utils import get_config, get_multi_level_value, get_value
import traceback
import pytz

running = False

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
                reviews = wk_api.get_reviews_completed_yesterday(user.token)
                lessons = wk_api.get_lessons_completed_yesterday(user.token)
                data[user.id] = {
                    'reviews': len(reviews),
                    'lessons': len(lessons)
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
    try:
        user_name = bot.user.name
        icon_url = bot.user.avatar_url
        channel = bot.get_channel(int(get_config('channel_id')))
        embed = discord.Embed(title=f'Daily WaniKani Summary', color=0xFF5733)
        embed.set_author(name=user_name, icon_url=icon_url)

        message = ''
        for user_id, wk_data in data.items():
            user = channel.guild.get_member(user_id)
            lessons = wk_data['lessons']
            reviews = wk_data['reviews']
            message += f'Completed {lessons} lessons, and {reviews} reviews'
            embed.add_field(name=user.display_name, value=message, inline=False)
        await channel.send(embed=embed)    
    except Exception as e:
        s = traceback.format_exc()
        content = f'Ignoring exception\n{s}'
        logtofile(content, 'error')

def get_seconds_until_next_day_pacific_time():
    day_delta = datetime.timedelta(days=1)
    now = datetime.datetime.now(pytz.timezone('America/Los_Angeles'))
    next_day = (now + day_delta).replace(microsecond=0, second=0, minute=1, hour=0)
    wait_seconds = (next_day - now).seconds
    return wait_seconds
