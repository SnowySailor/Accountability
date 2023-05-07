import discord
from discord.ext import commands
import traceback

from src.utils.utils import get_config
from src.utils.logger import init_logger, logtofile, logtodiscord
from src.internals.database import init_db, run_migrations
from src.internals.redis import init_redis

from src.tasks.critical_checks import CriticalChecks
from src.tasks.daily_summary import DailySummary
from src.tasks.daily_review_warning import DailyReviewWarning
from src.tasks.user_level_up_notifier import UserLevelUpNotifier

from src.cogs.activity_log import ActivityLog
from src.cogs.wanikani import WaniKani
from src.cogs.general import General
from src.cogs.user import User

class CustomBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        self.prepare_for_startup()
        await bot.add_cog(General())
        await bot.add_cog(WaniKani())
        await bot.add_cog(ActivityLog())
        await bot.add_cog(User())


    async def on_ready(self):
        await self.init_tasks()
        logtofile(f'Logged in as {bot.user} (ID: {bot.user.id})')
        logtofile('------')

    async def on_command_error(self, ctx, err):
        err = getattr(err, 'original', err)
        lines = ''.join(traceback.format_exception(err.__class__, err, err.__traceback__))
        lines = f'Ignoring exception in command {ctx.command}:\n{lines}'
        await logtodiscord(f'```{lines}```', bot, 'error')

    async def on_error(self, event, *args, **kwargs):
        trace = traceback.format_exc()
        await logtodiscord(f'```{trace}```', bot, 'error')

    async def init_tasks(self):
        self.loop.create_task(CriticalChecks(self).start())
        self.loop.create_task(DailyReviewWarning(self).start())
        self.loop.create_task(DailySummary(self).start())
        self.loop.create_task(UserLevelUpNotifier(self).start())

    def prepare_for_startup(self):
        run_migrations()
        init_db()
        init_redis()

init_logger()

intents = discord.Intents.default()
intents.members = True
intents.guild_messages = True
intents.message_content = True

bot = CustomBot(command_prefix=get_config('command_prefix', default = ';'), intents=intents)

def run_bot():
    bot.run(get_config('token'))
