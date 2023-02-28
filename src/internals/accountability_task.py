from src.utils.logger import logtofile, logtodiscord
from src.internals.sync import get_lock
from src.utils.time import get_seconds_until_next_hour
from discord.ext import commands
import traceback
import asyncio

running_tasks = set()

class AccountabilityTask:
    def __init__(self, type: str, bot: commands.Bot, target):
        self.type = type
        self.bot = bot
        self.target = target

    async def start(self):
        global running_tasks
        with get_lock(self.type):
            if self.type in running_tasks:
                return
            running_tasks.add(self.type)

        try:
            while True:
                await self.target(self.bot)
        except:
            try:
                with get_lock(self.type):
                    running_tasks.remove(self.type)
            except KeyError:
                pass

            sleep_time = get_seconds_until_next_hour() - 60
            if sleep_time < 0:
                sleep_time = 60

            trace = traceback.format_exc()
            message = f'Exception in `{self.type}` (restarting task in {sleep_time} seconds):\n```{content}\n```'
            logtofile(message, 'error')
            await logtodiscord(message, bot)
            await self.send_error_to_discord(trace, sleep_time)
            await asyncio.sleep(sleep_time)
        await self.start()
