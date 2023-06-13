from discord.ext import commands

class General(commands.Cog):
    @commands.command()
    async def ping(self, ctx, *msg: str):
        resp = ' '.join(msg)
        await ctx.send(resp)

    @commands.command()
    async def version(self, ctx):
        timestamp = ''
        commit = ''
        with open('/build-timestamp.txt', 'r') as f:
            timestamp = f.read().strip()
        with open('/build-commit.txt', 'r') as f:
            commit = f.read().strip()
        await ctx.send('Running commit `' + commit + '` (built `' + timestamp + '`)')
