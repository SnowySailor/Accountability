import discord
from discord.ext import commands
import random

# from database import get_cursor, init_db
from utils import get_config
from sync import get_lock
import logs

intents = discord.Intents.default()
intents.members = True
intents.guild_messages = True

bot = commands.Bot(command_prefix=';', intents=intents)

@bot.event
async def on_ready():
    # init_db()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command()
async def log(ctx, *log_words: str):
    log = ' '.join(log_words)
    user_id = ctx.author.id
    with get_lock('{user_id}:logs'):
        logs.create_log_for_user(user_id, log)
    await ctx.send('Logged activity for {ctx.author.mention}')

@bot.command()
async def rmlog(ctx, index: int):
    user_id = ctx.author.id
    today = get_current_day_for_user(user_id)
    async with get_lock('{user_id}:logs'):
        logs_today = logs.get_logs_for_user_for_specific_day(user_id, today)
        if len(logs_today) <= index:
            await ctx.send('{ctx.author.mention} Could not find log with that index')
            return
        logs.remove_log(logs_today[index].id)
    await ctx.send('{ctx.author.mention} Removed log at index {index}')

bot.run(get_config('token'))
