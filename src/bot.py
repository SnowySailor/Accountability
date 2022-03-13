import discord
from discord.ext import commands
import random
import logging
import sys
import traceback

from src.utils.utils import get_config
from src.utils.logger import init_logger, logtofile
from src.internals.database import init_db, run_migrations
from src.internals.sync import get_lock
import src.lib.logs
import src.lib.user

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
async def log(ctx, *log_words: str):
    log = ' '.join(log_words)
    user_id = ctx.author.id
    with get_lock(f'{user_id}:logs'):
        logs.create_log_for_user(user_id, log)
    await ctx.send(f'Logged activity for {ctx.author.mention}')

@bot.command()
async def rmlog(ctx, index: int):
    user_id = ctx.author.id
    time = user.get_current_time_for_user(user_id)
    with get_lock(f'{user_id}:logs'):
        logs_today = logs.get_logs_for_user_for_specific_day(user_id, time.date())
        if len(logs_today) <= index:
            await ctx.send(f'{ctx.author.mention} Could not find log with that index')
            return
        logs.remove_log(logs_today[index].id)
    await ctx.send(f'{ctx.author.mention} Removed log at index {index}')

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
    # print(content, file=sys.stderr)
    logtofile(content, 'error')

def run_bot():
    bot.run(get_config('token'))
