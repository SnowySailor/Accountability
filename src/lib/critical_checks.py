import asyncio
from discord.ext import commands
from src.utils.logger import logtofile
import src.lib.user as user_lib
import src.lib.wanikani
from src.utils.utils import get_config, get_multi_level_value, get_value
from src.utils.time import get_seconds_until_next_hour
import traceback

running = False

async def do_critical_checks(bot: commands.Bot) -> None:
    global running
    if running:
        return

    try:
        running = True
        await asyncio.sleep(get_seconds_until_next_hour())
        while True:
            users = user_lib.get_users_with_api_tokens()
            users_to_notify = []
            for user in users:
                assignments = wanikani.api.get_new_assignments_this_hour(user.token)
                for assignment in assignments:
                    if get_multi_level_value(assignment, 'data', 'srs_stage', default=6) < 5 and get_multi_level_value(assignment, 'data', 'subject_type') in ['radical', 'kanji']:
                        subject_id = get_multi_level_value(assignment, 'data', 'subject_id')
                        subject = wanikani.get_subject(subject_id, user.token)
                        wk_user = wanikani.get_user(user.token)
                        if get_value(subject, 'level') == get_value(wk_user, 'level'):
                            users_to_notify.append(user.id)
                            break
            if len(users_to_notify) > 0:
                await notify_of_new_criticals(users_to_notify, bot)
            await asyncio.sleep(get_seconds_until_next_hour())
    except:
        s = traceback.format_exc()
        content = f'Ignoring exception\n{s}'
        logtofile(content, 'error')
        running = False
        await do_critical_checks(bot)

async def notify_of_new_criticals(users_to_notify: list, bot: commands.Bot) -> None:
    channel = bot.get_channel(int(get_config('channel_id')))
    mentions_string = ''
    for user_id in users_to_notify:
        member = channel.guild.get_member(user_id)
        mentions_string += member.mention + ' '
    await channel.send(f'{mentions_string}you have criticals up for review')
