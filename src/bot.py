import discord
from discord.ext import commands
import random
import logging
import sys
import traceback

from src.utils.utils import get_config, LoggerWriter
from src.internals.database import init_db, run_migrations
from src.internals.sync import get_lock
import src.lib.logs
import src.lib.user

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
sys.stderr = LoggerWriter(logger.warning)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.members = True
intents.guild_messages = True

bot = commands.Bot(command_prefix=';', intents=intents)

@bot.event
async def on_ready():
    run_migrations()
    init_db()
    logger.debug(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logger.debug('------')

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
    if isinstance(err, commands.CommandInvokeError):
        logger.exception(err.__cause__)
        traceback = err.__cause__.__traceback__
        while traceback:
            logger.exception("{}: {}".format(traceback.tb_frame.f_code.co_filename,traceback.tb_lineno))
            traceback = traceback.tb_next

def run_bot():
    bot.run(get_config('token'))
