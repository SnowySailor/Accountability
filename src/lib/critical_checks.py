from threading import Thread
import asyncio
import datetime
from discord.ext import commands
from src.utils.logger import logtofile
import src.lib.user as user_lib
import src.lib.wk_api as wk_api
from src.utils.utils import get_config, get_value
import traceback

async def do_critical_checks(bot: commands.Bot) -> None:
    await asyncio.sleep(get_seconds_until_next_hour())
    while True:
        users = user_lib.get_users_with_api_tokens()
        for user in users:
            assignments = wk_api.get_new_assignments_this_hour(user['token'])
            for assignment in assignments:
                if get_value(assignment, 'srs_stage', 0) < 5 and get_value(assignment, 'subject_type') in ['radical', 'kanji']:
                    await notify_of_new_criticals(user['user_id'], bot)
                    break
        await asyncio.sleep(get_seconds_until_next_hour())

async def notify_of_new_criticals(user_id, bot):
    try:
        channel = bot.get_channel(int(get_config('channel_id')))
        await channel.send(f'<@{user_id}> you have criticals up for review')
    except Exception as e:
        s = traceback.format_exc()
        content = f'Ignoring exception\n{s}'
        logtofile(content, 'error')

def get_seconds_until_next_hour():
    delta = datetime.timedelta(hours=1)
    now = datetime.datetime.now()
    next_hour = (now + delta).replace(microsecond=0, second=0, minute=1)
    wait_seconds = (next_hour - now).seconds
    return wait_seconds