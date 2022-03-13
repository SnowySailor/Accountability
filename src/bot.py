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
async def log(ctx, *message_words: str):
    message = ' '.join(message_words)
    user_id = ctx.author.id
    server_id = ctx.guild.id
    with get_lock(f'{user_id}:activities'):
        activity.log_activity_for_user(user_id, server_id, message)
    await ctx.send(f'Logged activity for {ctx.author.mention}')

@bot.command()
async def rmlog(ctx, index: int):
    user_id = ctx.author.id
    server_id = ctx.guild.id
    lock_key = f'{user_id}:activities'
    l = is_locked(lock_key)
    if l:
        await ctx.send(f'{ctx.author.mention} somehow you hit a race condition. Nothing has been removed.')
        return

    # Theoretically a race condition here after checking if the lock is locked before locking again
    with get_lock(lock_key):
        activities_today = activity.get_activities_for_user_for_today(user_id, server_id)
        if len(activities_today) <= index:
            await ctx.send(f'{ctx.author.mention} Could not find log with that index')
            return
        activity.remove_activity(activities_today[index].id)
    await ctx.send(f'{ctx.author.mention} Removed log at index {index}')

@bot.command()
async def show(ctx):
    user_id = ctx.author.id
    server_id = ctx.guild.id
    activities_today = activity.get_activities_for_user_for_today(user_id, server_id)
    if len(activities_today) == 0:
        await ctx.send(f'{ctx.author.mention} You have no activities logged today')
    else:
        string = ''
        for act in activities_today:
            string += act.activity + '\n\n'
        await ctx.send(f'{ctx.author.mention}\'s activies today:\n{string}')

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
