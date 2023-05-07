from discord.ext import commands
import discord

import src.lib.wk_api as wk_api
import src.lib.user as user

class WaniKani(commands.Cog):
    @commands.command(help="Sets your WaniKani token (Japanese channel only)")
    async def settoken(self, ctx, token):
        user_id = ctx.author.id
        user.set_wanikani_api_token_for_user(user_id, token)
        await ctx.send('Set token')

    @commands.command(help="Clears your WaniKani token (Japanese channel only)")
    async def cleartoken(self, ctx):
        user_id = ctx.author.id
        user.remove_wanikani_api_token_for_user(user_id)
        await ctx.send('Cleared token')

    @commands.command(help="Show information about a WaniKani user (Japanese channel only)")
    async def wkstats(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        user_id = member.id

        token = user.get_wanikani_api_token(user_id)
        if token is None:
            await ctx.send('User does not have their WaniKani API token saved')
            return

        infos = []
        stats = await wk_api.get_user_stats(token)
        for key, value in stats.items():
            infos.append(key + ': ' + str(value))
        embed = discord.Embed(title=f'{member.display_name}\'s WaniKani Stats', description='\n'.join(infos), color=0xFF5733)
        await ctx.send(embed=embed)

    @wkstats.error
    async def wkstats_error_handler(self, ctx, error):
        if isinstance(error, commands.errors.MemberNotFound):
            await ctx.send("Invalid user")