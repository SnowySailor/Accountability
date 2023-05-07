from discord.ext import commands

import src.lib.user as user

class User(commands.Cog):
    @commands.command(help="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones", description="Sets timezones. See <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones> for a list of timezones. Example: America/Los_Angeles")
    async def settz(self, ctx, timezone: str):
        user_id = ctx.author.id
        result = user.set_timezone_for_user(user_id, timezone)
        if not result:
            await ctx.send(f'{ctx.author.mention} Invalid timezone. See list here: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>')
        else:
            await ctx.send(f'{ctx.author.mention} Timezone set to {timezone}')

