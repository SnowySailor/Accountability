from src.utils.logger import logtofile, logtodiscord
from src.internals.sync import get_lock
from src.utils.time import get_seconds_until_next_hour
from discord.ext import commands
import traceback
import asyncio

running_tasks = set()

class AccountabilityTask:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.type = ''

    async def start(self):
        global running_tasks
        with get_lock(self.type):
            if self.type in running_tasks:
                return
            running_tasks.add(self.type)

        try:
            while True:
                await self.looping_task()
        except:
            try:
                with get_lock(self.type):
                    running_tasks.remove(self.type)
            except KeyError:
                pass

            trace = traceback.format_exc()
            message = f'Exception in `{self.type}`:\n```{trace}\n```'
            logtofile(message, 'error')
            await logtodiscord(message, self.bot)
        await self.start()

    def looping_task(self):
        raise NotImplementedError("looping_task not implemented")
