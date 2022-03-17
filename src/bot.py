import discord
from discord.ext import commands
import random
import logging
import sys
import traceback

from src.utils.utils import get_config
from src.utils.logger import init_logger, logtofile
from src.internals.database import init_db, run_migrations
from src.internals.sync import get_lock, is_locked
import src.lib.activity as activity
import src.lib.user as user
import src.lib.category as category
import src.lib.default_category as default_category

intents = discord.Intents.default()
intents.members = True
intents.guild_messages = True

init_logger()

bot = commands.Bot(command_prefix=';', intents=intents)

@bot.event
async def on_ready():
    run_migrations()
    init_db()
    logtofile(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logtofile('------')

@bot.command()
async def ping(ctx, *msg: str):
    resp = ' '.join(msg)
    await ctx.send(resp)

@bot.command()
async def log(ctx, *description: str):
    user_id = ctx.author.id
    server_id = ctx.guild.id
    description = ' '.join(description)

    if len(description) == 0:
        await ctx.send(f'{ctx.author.mention} Description cannot be empty')
        return

    if len(description) > 2000:
        await ctx.send(f'{ctx.author.mention} Please keep descriptions under 2,000 characters')
        return

    with get_lock(f'{user_id}:{server_id}:activities'):
        activity.log_activity_for_user(user_id, server_id, description)
    await ctx.send(f'Logged activity for {ctx.author.mention}')

@bot.command()
async def rmlog(ctx, index: int):
    user_id = ctx.author.id
    server_id = ctx.guild.id
    lock_key = f'{user_id}:{server_id}:activities'
    if is_locked(lock_key):
        await ctx.send(f'{ctx.author.mention} somehow you hit a race condition. Nothing has been removed.')
        return

    # Theoretically a race condition here after checking if the lock is locked before locking again
    with get_lock(lock_key):
        activities_today = activity.get_activities_for_user_for_today(user_id, server_id)
        if len(activities_today) <= index:
            await ctx.send(f'{ctx.author.mention} Could not find activity with that index')
            return
        activity.remove_activity(activities_today[index].id)
    await ctx.send(f'{ctx.author.mention} Removed activity at index {index}')

@bot.command()
async def show(ctx):
    user_id = ctx.author.id
    server_id = ctx.guild.id
    activities_today = activity.get_activities_for_user_for_today(user_id, server_id)

    description = ''
    if len(activities_today) == 0:
        description = 'No activities logged today'

    embed = discord.Embed(title=f'{ctx.author}\'s Activities Today', description=description, color=0xFF5733)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    for category in activities_today:
        if category is None:
            category = 'No Category'
        escaped_category = discord.utils.escape_mentions(category)
        description = ''
        for idx, activity in enumerate(category):
            description += f'{idx + 1}. {activity.description}'
        description = discord.utils.escape_mentions(description)
        embed.add_field(name=escaped_category, value=description, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def edit(ctx, index: int, *new_description: str):
    user_id = ctx.author.id
    server_id = ctx.guild.id
    new_description = ' '.join(new_description)

    if len(new_description) > 2000:
        await ctx.send(f'{ctx.author.mention} Please keep descriptions under 2,000 characters')
        return

    if len(new_description) == 0:
        await ctx.send(f'{ctx.author.mention} Description cannot be empty')
        return

    activities_today = activity.get_activities_for_user_for_today(user_id, server_id)
    if len(activities_today) <= index:
        await ctx.send(f'{ctx.author.mention} Could not find activity with that index')
        return

    with get_lock(f'{user_id}:{server_id}:activities'):
        activity.update_activity_description(activities_today[index].id, new_description)
    await ctx.send(f'{ctx.author.mention} Activity updated')

@bot.command()
async def settz(ctx, timezone: str):
    user_id = ctx.author.id
    result = user.set_timezone_for_user(user_id, timezone)
    if not result:
        await ctx.send(f'{ctx.author.mention} Invalid timezone. See list here: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>')
    else:
        await ctx.send(f'{ctx.author.mention} Timezone set to {timezone}')

@bot.command()
async def addcat(ctx, name: str):
    user_id = ctx.author.id
    server_id = ctx.guild.id

    default_cat = default_category.get_default_category_by_name(name)
    if default_cat is not None:
        if default_category.is_user_opted_out_of_default_category(user_id, server_id, default_cat.id):
            default_category.opt_into_default_category(user_id, server_id, default_cat.id)
            await ctx.send(f'{ctx.author.mention} Category created')
        else:
            await ctx.send(f'{ctx.author.mention} `{name}` already exists as a default category')
        return

    result = category.create_category_for_user(user_id, server_id, name)
    if result is None:
        await ctx.send(f'{ctx.author.mention} Category already exists')
    else:
        await ctx.send(f'{ctx.author.mention} Category created')

@bot.command()
async def editcat(ctx, old_name: str, new_name: str):
    user_id = ctx.author.id
    server_id = ctx.guild.id

    result = category.get_category_by_name(user_id, server_id, new_name)
    if result is not None:
        await ctx.send(f'{ctx.author.mention} Category `{new_name}` already exists')
        return

    default_cat = default_category.get_default_category_by_name(new_name)
    if default_cat is not None:
        await ctx.send(f'{ctx.author.mention} `{new_name}` already exists as a default category')
        return

    result = category.get_category_by_name(user_id, server_id, old_name)
    if result is None:
        await ctx.send(f'{ctx.author.mention} Category does not exist')
        return
    else:
        category.update_category_name(result.id, new_name)
        await ctx.send(f'{ctx.author.mention} Category updated from `{result.display_name}` to `{new_name}`')

@bot.command()
async def rmcat(ctx, name: str, force: str = None):
    user_id = ctx.author.id
    server_id = ctx.guild.id

    result = default_category.get_default_category_by_name(name)
    if result is not None:
        if default_category.is_category_being_used_by_activity(user_id, server_id, result.id) and force != 'FORCE':
            await ctx.send(f'{ctx.author.mention} That category has activities associated with it. Run `;rmcat "{name}" FORCE` to force removal. Activities with this category will have the category removed.')
        else:
            default_category.opt_out_of_default_category(user_id, server_id, result.id)
            await ctx.send(f'{ctx.author.mention} Category `{name}` deleted')
    else:
        result = category.get_category_by_name(user_id, server_id, name)
        if result is None:
            if result is None:
                await ctx.send(f'{ctx.author.mention} Category does not exist')
        else:
            if category.is_category_being_used_by_activity(user_id, server_id, result.id) and force != 'FORCE':
                await ctx.send(f'{ctx.author.mention} That category has activities associated with it. Run `;rmcat "{name}" FORCE` to force removal. Activities with this category will have the category removed.')
            else:
                category.delete_category(result.id)
                await ctx.send(f'{ctx.author.mention} Category `{name}` deleted')

@bot.command()
async def lscats(ctx):
    user_id = ctx.author.id
    server_id = ctx.guild.id
    custom_categories = category.get_categories_for_user(user_id, server_id)
    default_categories = default_category.get_default_categories_for_user(user_id, server_id)

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

    custom_description.strip()
    default_description.strip()
    custom_description = discord.utils.escape_mentions(custom_description)
    default_description = discord.utils.escape_mentions(default_description)

    embed = discord.Embed(title=f'{ctx.author}\'s Categories', color=0xFF5733)
    if len(custom_categories) > 0:
        embed.add_field(name=f'Custom Categories', value=custom_description, inline=False)
    if len(default_categories) > 0:
        embed.add_field(name=f'Default Categories', value=default_description, inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, err):
    err = getattr(err, 'original', err)
    lines = ''.join(traceback.format_exception(err.__class__, err, err.__traceback__))
    lines = f'Ignoring exception in command {ctx.command}:\n{lines}'
    logtofile(lines, 'error')

@bot.event
async def on_error(event, *args, **kwargs):
    s = traceback.format_exc()
    content = f'Ignoring exception in {event}\n{s}'
    logtofile(content, 'error')

def run_bot():
    bot.run(get_config('token'))
