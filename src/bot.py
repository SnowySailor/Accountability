import discord
from discord.ext import commands
import random
import logging
import sys
import traceback

from src.utils.utils import get_config
from src.utils.logger import init_logger, logtofile, logtodiscord
from src.internals.database import init_db, run_migrations
from src.internals.redis import init_redis
from src.internals.sync import get_lock, is_locked
import src.lib.activity as activity
import src.lib.user as user
import src.lib.category as category
import src.lib.default_category as default_category
import src.lib.wk_api as wk_api
from src.tasks.critical_checks import CriticalChecks
from src.tasks.daily_summary import DailySummary
from src.tasks.daily_review_warning import DailyReviewWarning
from src.tasks.user_level_up_notifier import UserLevelUpNotifier

init_logger()

intents = discord.Intents.default()
intents.members = True
intents.guild_messages = True
intents.message_content = True

class CustomBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        self.prepare_for_startup()

    async def on_ready(self):
        await self.init_tasks()
        logtofile(f'Logged in as {bot.user} (ID: {bot.user.id})')
        logtofile('------')

    async def init_tasks(self):
        self.loop.create_task(CriticalChecks(self).start())
        self.loop.create_task(DailyReviewWarning(self).start())
        self.loop.create_task(DailySummary(self).start())
        self.loop.create_task(UserLevelUpNotifier(self).start())

    def prepare_for_startup(self):
        run_migrations()
        init_db()
        init_redis()

bot = CustomBot(command_prefix=get_config('command_prefix', default = ';'), intents=intents)

@bot.command()
async def ping(ctx, *msg: str):
    resp = ' '.join(msg)
    await ctx.send(resp)

@bot.command(help="Logs an Activity with no category")
async def log(ctx, *description: str):
    user_id = ctx.author.id
    channel_id = ctx.channel.id
    description = ' '.join(description)

    if len(description) == 0:
        await ctx.send(f'{ctx.author.mention} Description cannot be empty')
        return

    if len(description) > 2000:
        await ctx.send(f'{ctx.author.mention} Please keep descriptions under 2,000 characters')
        return

    with get_lock(f'{user_id}:{channel_id}:activities'):
        activity.log_activity_for_user(user_id, channel_id, description)
    await ctx.send(f'Logged activity for {ctx.author.mention}')

@bot.command(help="Logs an Activity with a category")
async def logc(ctx, category_name: str, *description: str):
    user_id = ctx.author.id
    channel_id = ctx.channel.id
    description = ' '.join(description)

    if len(description) == 0:
        await ctx.send(f'{ctx.author.mention} Description cannot be empty')
        return

    if len(description) > 2000:
        await ctx.send(f'{ctx.author.mention} Please keep descriptions under 2,000 characters')
        return

    default = default_category.get_default_category_by_name_for_user(user_id, channel_id, category_name)
    cat = category.get_category_by_name(user_id, channel_id, category_name)
    if cat is None and default is None:
        await ctx.send(f'{ctx.author.mention} Category `{category_name}` does not exist')
        return
    else:
        cat_id = cat.id if cat is not None else None
        default_id = default.id if default is not None else None
        with get_lock(f'{user_id}:{channel_id}:activities'):
            activity.log_activity_for_user(user_id, channel_id, description, cat_id, default_id)
        await ctx.send(f'Logged activity for {ctx.author.mention}')

@bot.command(help="Removes a logs", description="You give the index (starts at 0) and the category name (if you have multiple categories). If it has no category, you can omit the category name.")
async def rmlog(ctx, index: int, category_name: str = None):
    user_id = ctx.author.id
    channel_id = ctx.channel.id
    lock_key = f'{user_id}:{channel_id}:activities'
    if is_locked(lock_key):
        await ctx.send(f'{ctx.author.mention} somehow you hit a race condition. Nothing has been removed.')
        return

    # Theoretically a race condition here after checking if the lock is locked before locking again
    with get_lock(lock_key):
        activities_today = activity.get_activities_for_user_for_today(user_id, channel_id)
        if category_name not in activities_today:
            await ctx.send(f'{ctx.author.mention} You do not have an activity in that category')
            return
        if len(activities_today[category_name]) <= index:
            await ctx.send(f'{ctx.author.mention} Could not find an activity in the category')
            return
        activity.remove_activity(activities_today[category_name][index].id)
    await ctx.send(f'{ctx.author.mention} Removed activity at index {index}')

@bot.command(help="Shows your activities for today. Optional username")
async def show(ctx, *name: str):
    name = ' '.join(name)
    if len(name) != 0:
        user = discord.Guild.get_member_named(ctx.guild, name)
        if user is None:
            await ctx.send(f'{ctx.author.mention} Could not find user {name}')
            return
        user_name = user.name
        user_id = user.id
    else:
        user_name = ctx.author.name
        user_id = ctx.author.id
    channel_id = ctx.channel.id
    activities_today = activity.get_activities_for_user_for_today(user_id, channel_id)

    description = ''
    if len(activities_today) == 0:
        description = 'No activities logged today'

    embed = discord.Embed(title=f'{user_name}\'s Activities Today', description=description, color=0xFF5733)
    embed.set_author(name=user_name)
    for cat, activity_list in activities_today.items():
        if cat is None:
            cat = 'No Category'
        escaped_category = discord.utils.escape_mentions(cat)
        description = ''
        for idx, act in enumerate(activity_list):
            description += f'{idx + 1}. {act.description}\n'
        description = discord.utils.escape_mentions(description).strip()
        embed.add_field(name=escaped_category, value=description, inline=False)
    await ctx.send(embed=embed)

@bot.command(help="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones", description="Sets timezones. See <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones> for a list of timezones. Example: America/Los_Angeles")
async def settz(ctx, timezone: str):
    user_id = ctx.author.id
    result = user.set_timezone_for_user(user_id, timezone)
    if not result:
        await ctx.send(f'{ctx.author.mention} Invalid timezone. See list here: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>')
    else:
        await ctx.send(f'{ctx.author.mention} Timezone set to {timezone}')

@bot.command(help="Add a category")
async def addcat(ctx, name: str = ''):
    user_id = ctx.author.id
    channel_id = ctx.channel.id
    name = name.strip()

    if len(name) == 0:
        await ctx.send(f'{ctx.author.mention} Please provide a category name')
        return

    if len(name) > 50:
        await ctx.send(f'{ctx.author.mention} Category name must be 50 characters or fewer')
        return

    default_cat = default_category.get_default_category_by_name(name)
    if default_cat is not None:
        if default_category.is_user_opted_out_of_default_category(user_id, channel_id, default_cat.id):
            default_category.opt_into_default_category(user_id, channel_id, default_cat.id)
            await ctx.send(f'{ctx.author.mention} Category created')
        else:
            await ctx.send(f'{ctx.author.mention} `{name}` already exists as a default category')
        return

    result = category.create_category_for_user(user_id, channel_id, name)
    if result is None:
        await ctx.send(f'{ctx.author.mention} Category already exists')
    else:
        await ctx.send(f'{ctx.author.mention} Category created')

@bot.command(help="Change a category name", description="Old name then new name")
async def editcat(ctx, old_name: str, new_name: str):
    user_id = ctx.author.id
    channel_id = ctx.channel.id
    new_name = new_name.strip()

    if len(new_name) == 0:
        await ctx.send(f'{ctx.author.mention} Please provide a category name')
        return

    if len(new_name) > 50:
        await ctx.send(f'{ctx.author.mention} Category name must be 50 characters or fewer')
        return

    result = category.get_category_by_name(user_id, channel_id, new_name)
    if result is not None:
        await ctx.send(f'{ctx.author.mention} Category `{new_name}` already exists')
        return

    default_cat = default_category.get_default_category_by_name(new_name)
    if default_cat is not None:
        await ctx.send(f'{ctx.author.mention} `{new_name}` already exists as a default category')
        return

    result = category.get_category_by_name(user_id, channel_id, old_name)
    if result is None:
        await ctx.send(f'{ctx.author.mention} Category does not exist')
        return
    else:
        category.update_category_name(result.id, new_name)
        await ctx.send(f'{ctx.author.mention} Category updated from `{result.display_name}` to `{new_name}`')

@bot.command(help="Removes a category", description="Use FORCE to remove a category that has activities associated with it.")
async def rmcat(ctx, name: str, force: str = None):
    user_id = ctx.author.id
    channel_id = ctx.channel.id

    result = default_category.get_default_category_by_name(name)
    if result is not None:
        if default_category.is_category_being_used_by_activity(user_id, channel_id, result.id) and force != 'FORCE':
            await ctx.send(f'{ctx.author.mention} That category has activities associated with it. Run `;rmcat "{name}" FORCE` to force removal. Activities with this category will have the category removed.')
        else:
            default_category.opt_out_of_default_category(user_id, channel_id, result.id)
            await ctx.send(f'{ctx.author.mention} Category `{name}` deleted')
    else:
        result = category.get_category_by_name(user_id, channel_id, name)
        if result is None:
            if result is None:
                await ctx.send(f'{ctx.author.mention} Category does not exist')
        else:
            if category.is_category_being_used_by_activity(user_id, channel_id, result.id) and force != 'FORCE':
                await ctx.send(f'{ctx.author.mention} That category has activities associated with it. Run `;rmcat "{name}" FORCE` to force removal. Activities with this category will have the category removed.')
            else:
                category.delete_category(result.id)
                await ctx.send(f'{ctx.author.mention} Category `{name}` deleted')

@bot.command(help="Lists all your categories")
async def lscats(ctx):
    user_id = ctx.author.id
    channel_id = ctx.channel.id
    custom_categories = category.get_categories_for_user(user_id, channel_id)
    default_categories = default_category.get_default_categories_for_user(user_id, channel_id)

    if len(custom_categories) == 0 and len(default_categories) == 0:
        await ctx.send(f'{ctx.author.mention} No categories defined yet')
        return

    custom_description = ''
    for idx, cat in enumerate(custom_categories):
        display_name = discord.utils.escape_markdown(cat.display_name)
        custom_description += f'{idx + 1}. {display_name}\n'

    default_description = ''
    for idx, cat in enumerate(default_categories):
        display_name = discord.utils.escape_markdown(cat.display_name)
        default_description += f'{idx + 1}. {display_name}\n'

    custom_description = discord.utils.escape_mentions(custom_description).strip()
    default_description = discord.utils.escape_mentions(default_description).strip()

    embed = discord.Embed(title=f'{ctx.author}\'s Categories', color=0xFF5733)
    if len(custom_categories) > 0:
        embed.add_field(name=f'Custom Categories', value=custom_description, inline=False)
    if len(default_categories) > 0:
        embed.add_field(name=f'Default Categories', value=default_description, inline=False)
    await ctx.send(embed=embed)

@bot.command(help="Sets your WaniKani token (Japanese channel only)")
async def settoken(ctx, token):
    user_id = ctx.author.id
    user.set_wanikani_api_token_for_user(user_id, token)
    await ctx.send('Set token')

@bot.command(help="Clears your WaniKani token (Japanese channel only)")
async def cleartoken(ctx):
    user_id = ctx.author.id
    user.remove_wanikani_api_token_for_user(user_id)
    await ctx.send('Cleared token')

@bot.command(help="Show information about a WaniKani user (Japanese channel only)")
async def wkstats(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    user_id = member.id

    token = user.get_wanikani_api_token(user_id)
    if token is None:
        await ctx.send('User does not have their WaniKani API token saved')
        return

    infos = []
    stats = await wk_api.get_user_stats(token)
    for key, value in stats.items():
        infos.append(key + ': ' + str(value))
    embed = discord.Embed(title=f'{member.display_name}\'s WaniKani Stats', description='\n'.join(infos), color=0xFF5733)
    await ctx.send(embed=embed)

@wkstats.error
async def wkstats_error_handler(ctx, error):
    if isinstance(error, commands.errors.MemberNotFound):
        await ctx.send("Invalid user")

@bot.event
async def on_command_error(ctx, err):
    err = getattr(err, 'original', err)
    lines = ''.join(traceback.format_exception(err.__class__, err, err.__traceback__))
    lines = f'Ignoring exception in command {ctx.command}:\n{lines}'
    await logtodiscord(f'```{lines}```', bot, 'error')

@bot.event
async def on_error(event, *args, **kwargs):
    trace = traceback.format_exc()
    await logtodiscord(f'```{trace}```', bot, 'error')

def run_bot():
    bot.run(get_config('token'))
