from discord.ext import commands
import discord

from src.internals.sync import get_lock, is_locked

import src.lib.activity as activity
import src.lib.user as user
import src.lib.category as category
import src.lib.default_category as default_category

class ActivityLog(commands.Cog):
    @commands.command(help="Logs an Activity with no category")
    async def log(self, ctx, *description: str):
        user_id = ctx.author.id
        channel_id = ctx.channel.id
        description = ' '.join(description)

        if len(description) == 0:
            await ctx.send(f'{ctx.author.mention} Description cannot be empty')
            return

        if len(description) > 2000:
            await ctx.send(f'{ctx.author.mention} Please keep descriptions under 2,000 characters')
            return

        with get_lock(f'{user_id}:{channel_id}:activities'):
            activity.log_activity_for_user(user_id, channel_id, description)
        await ctx.send(f'Logged activity for {ctx.author.mention}')

    @commands.command(help="Logs an Activity with a category")
    async def logc(self, ctx, category_name: str, *description: str):
        user_id = ctx.author.id
        channel_id = ctx.channel.id
        description = ' '.join(description)

        if len(description) == 0:
            await ctx.send(f'{ctx.author.mention} Description cannot be empty')
            return

        if len(description) > 2000:
            await ctx.send(f'{ctx.author.mention} Please keep descriptions under 2,000 characters')
            return

        default = default_category.get_default_category_by_name_for_user(user_id, channel_id, category_name)
        cat = category.get_category_by_name(user_id, channel_id, category_name)
        if cat is None and default is None:
            await ctx.send(f'{ctx.author.mention} Category `{category_name}` does not exist')
            return
        else:
            cat_id = cat.id if cat is not None else None
            default_id = default.id if default is not None else None
            with get_lock(f'{user_id}:{channel_id}:activities'):
                activity.log_activity_for_user(user_id, channel_id, description, cat_id, default_id)
            await ctx.send(f'Logged activity for {ctx.author.mention}')

    @commands.command(help="Removes a logs", description="You give the index (starts at 0) and the category name (if you have multiple categories). If it has no category, you can omit the category name.")
    async def rmlog(self, ctx, index: int, category_name: str = None):
        user_id = ctx.author.id
        channel_id = ctx.channel.id
        lock_key = f'{user_id}:{channel_id}:activities'
        if is_locked(lock_key):
            await ctx.send(f'{ctx.author.mention} somehow you hit a race condition. Nothing has been removed.')
            return

        # Theoretically a race condition here after checking if the lock is locked before locking again
        with get_lock(lock_key):
            activities_today = activity.get_activities_for_user_for_today(user_id, channel_id)
            if category_name not in activities_today:
                await ctx.send(f'{ctx.author.mention} You do not have an activity in that category')
                return
            if len(activities_today[category_name]) <= index:
                await ctx.send(f'{ctx.author.mention} Could not find an activity in the category')
                return
            activity.remove_activity(activities_today[category_name][index].id)
        await ctx.send(f'{ctx.author.mention} Removed activity at index {index}')

    @commands.command(help="Shows your activities for today. Optional username")
    async def show(self, ctx, *name: str):
        name = ' '.join(name)
        if len(name) != 0:
            user = discord.Guild.get_member_named(self, ctx.guild, name)
            if user is None:
                await ctx.send(f'{ctx.author.mention} Could not find user {name}')
                return
            user_name = user.name
            user_id = user.id
        else:
            user_name = ctx.author.name
            user_id = ctx.author.id
        channel_id = ctx.channel.id
        activities_today = activity.get_activities_for_user_for_today(user_id, channel_id)

        description = ''
        if len(activities_today) == 0:
            description = 'No activities logged today'

        embed = discord.Embed(title=f'{user_name}\'s Activities Today', description=description, color=0xFF5733)
        embed.set_author(name=user_name)
        for cat, activity_list in activities_today.items():
            if cat is None:
                cat = 'No Category'
            escaped_category = discord.utils.escape_mentions(cat)
            description = ''
            for idx, act in enumerate(activity_list):
                description += f'{idx + 1}. {act.description}\n'
            description = discord.utils.escape_mentions(description).strip()
            embed.add_field(name=escaped_category, value=description, inline=False)
        await ctx.send(embed=embed)

    @commands.command(help="Add a category")
    async def addcat(self, ctx, name: str = ''):
        user_id = ctx.author.id
        channel_id = ctx.channel.id
        name = name.strip()

        if len(name) == 0:
            await ctx.send(f'{ctx.author.mention} Please provide a category name')
            return

        if len(name) > 50:
            await ctx.send(f'{ctx.author.mention} Category name must be 50 characters or fewer')
            return

        default_cat = default_category.get_default_category_by_name(name)
        if default_cat is not None:
            if default_category.is_user_opted_out_of_default_category(user_id, channel_id, default_cat.id):
                default_category.opt_into_default_category(user_id, channel_id, default_cat.id)
                await ctx.send(f'{ctx.author.mention} Category created')
            else:
                await ctx.send(f'{ctx.author.mention} `{name}` already exists as a default category')
            return

        result = category.create_category_for_user(user_id, channel_id, name)
        if result is None:
            await ctx.send(f'{ctx.author.mention} Category already exists')
        else:
            await ctx.send(f'{ctx.author.mention} Category created')

    @commands.command(help="Change a category name", description="Old name then new name")
    async def editcat(self, ctx, old_name: str, new_name: str):
        user_id = ctx.author.id
        channel_id = ctx.channel.id
        new_name = new_name.strip()

        if len(new_name) == 0:
            await ctx.send(f'{ctx.author.mention} Please provide a category name')
            return

        if len(new_name) > 50:
            await ctx.send(f'{ctx.author.mention} Category name must be 50 characters or fewer')
            return

        result = category.get_category_by_name(user_id, channel_id, new_name)
        if result is not None:
            await ctx.send(f'{ctx.author.mention} Category `{new_name}` already exists')
            return

        default_cat = default_category.get_default_category_by_name(new_name)
        if default_cat is not None:
            await ctx.send(f'{ctx.author.mention} `{new_name}` already exists as a default category')
            return

        result = category.get_category_by_name(user_id, channel_id, old_name)
        if result is None:
            await ctx.send(f'{ctx.author.mention} Category does not exist')
            return
        else:
            category.update_category_name(result.id, new_name)
            await ctx.send(f'{ctx.author.mention} Category updated from `{result.display_name}` to `{new_name}`')

    @commands.command(help="Removes a category", description="Use FORCE to remove a category that has activities associated with it.")
    async def rmcat(self, ctx, name: str, force: str = None):
        user_id = ctx.author.id
        channel_id = ctx.channel.id

        result = default_category.get_default_category_by_name(name)
        if result is not None:
            if default_category.is_category_being_used_by_activity(user_id, channel_id, result.id) and force != 'FORCE':
                await ctx.send(f'{ctx.author.mention} That category has activities associated with it. Run `;rmcat "{name}" FORCE` to force removal. Activities with this category will have the category removed.')
            else:
                default_category.opt_out_of_default_category(user_id, channel_id, result.id)
                await ctx.send(f'{ctx.author.mention} Category `{name}` deleted')
        else:
            result = category.get_category_by_name(user_id, channel_id, name)
            if result is None:
                if result is None:
                    await ctx.send(f'{ctx.author.mention} Category does not exist')
            else:
                if category.is_category_being_used_by_activity(user_id, channel_id, result.id) and force != 'FORCE':
                    await ctx.send(f'{ctx.author.mention} That category has activities associated with it. Run `;rmcat "{name}" FORCE` to force removal. Activities with this category will have the category removed.')
                else:
                    category.delete_category(result.id)
                    await ctx.send(f'{ctx.author.mention} Category `{name}` deleted')

    @commands.command(help="Lists all your categories")
    async def lscats(self, ctx):
        user_id = ctx.author.id
        channel_id = ctx.channel.id
        custom_categories = category.get_categories_for_user(user_id, channel_id)
        default_categories = default_category.get_default_categories_for_user(user_id, channel_id)

        if len(custom_categories) == 0 and len(default_categories) == 0:
            await ctx.send(f'{ctx.author.mention} No categories defined yet')
            return

        custom_description = ''
        for idx, cat in enumerate(custom_categories):
            display_name = discord.utils.escape_markdown(cat.display_name)
            custom_description += f'{idx + 1}. {display_name}\n'

        default_description = ''
        for idx, cat in enumerate(default_categories):
            display_name = discord.utils.escape_markdown(cat.display_name)
            default_description += f'{idx + 1}. {display_name}\n'

        custom_description = discord.utils.escape_mentions(custom_description).strip()
        default_description = discord.utils.escape_mentions(default_description).strip()

        embed = discord.Embed(title=f'{ctx.author}\'s Categories', color=0xFF5733)
        if len(custom_categories) > 0:
            embed.add_field(name=f'Custom Categories', value=custom_description, inline=False)
        if len(default_categories) > 0:
            embed.add_field(name=f'Default Categories', value=default_description, inline=False)
        await ctx.send(embed=embed)
