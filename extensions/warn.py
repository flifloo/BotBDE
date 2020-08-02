import re

from discord import Embed, Forbidden, Member, Guild
from discord.ext import commands
from discord.ext.commands import BadArgument

from administrator import db
from administrator.logger import logger

extension_name = "warn"
logger = logger.getChild(extension_name)

channel_id_re = re.compile(r"^<#([0-9]+)>$")


class Warn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "Send warning to user and make custom action after a number of warn"

    @staticmethod
    def get_target(ctx: commands.Context, user: str) -> Member:
        users = {str(m): m for m in ctx.guild.members}
        if user not in users:
            raise BadArgument()
        return users[user]

    @commands.group("warn", pass_context=True)
    @commands.guild_only()
    #@commands.has_permissions(manage_roles=True, kick_members=True, ban_members=True, mute_members=True)
    async def warn(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.warn_help)

    @warn.group("help", pass_context=True)
    async def warn_help(self, ctx: commands.Context):
        embed = Embed(title="Warn help")
        embed.add_field(name="add <user> <description>", value="Send a warn to a user", inline=False)
        embed.add_field(name="remove <user> <number>", value="Remove a number of warn to a user", inline=False)
        embed.add_field(name="purge <user>", value="Remove all warn of a user", inline=False)
        embed.add_field(name="list [user]", value="List warn of the guild or a specified user", inline=False)
        await ctx.send(embed=embed)

    @warn.group("add", pass_context=True)
    async def warn_add(self, ctx: commands.Context, user: str, description: str):
        target = self.get_target(ctx, user)

        s = db.Session()
        s.add(db.Warn(target.id, ctx.author.id, ctx.guild.id, description))
        s.commit()
        s.close()

        try:
            embed = Embed(title="You get warned !", description="A moderator send you a warn", color=0xff0000)
            embed.add_field(name="Description:", value=description)
            await target.send(embed=embed)
        except Forbidden:
            await ctx.send("Fail to send warn notification to the user, DM close :warning:")
        else:
            await ctx.message.add_reaction("\U0001f44d")

    @warn.group("remove", pass_context=True)
    async def warn_remove(self, ctx: commands.Context, user: str, number: int):
        target = self.get_target(ctx, user)
        s = db.Session()
        ws = s.query(db.Warn).filter(db.Warn.guild == ctx.guild.id, db.Warn.user == target.id).all()
        if number <= 0 or number > len(ws):
            raise BadArgument()
        s.delete(ws[number-1])
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @warn.group("purge", pass_context=True)
    async def warn_purge(self, ctx: commands.Context, user: str):
        target = self.get_target(ctx, user)
        s = db.Session()
        for w in s.query(db.Warn).filter(db.Warn.guild == ctx.guild.id, db.Warn.user == target.id).all():
            s.delete(w)
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @warn.group("list", pass_context=True)
    async def warn_list(self, ctx: commands.Context, user: str = None):
        s = db.Session()
        embed = Embed(title="Warn list")
        ws = {}

        if user:
            target = self.get_target(ctx, user)
            ws[target.id] = s.query(db.Warn).filter(db.Warn.guild == ctx.guild.id, db.Warn.user == target.id).all()
        else:
            for w in s.query(db.Warn).filter(db.Warn.guild == ctx.guild.id).all():
                if w.user not in ws:
                    ws[w.user] = []
                ws[w.user].append(w)
        s.close()

        for u in ws:
            warns = [f"{w.date.strftime('%d/%m/%Y %H:%M')} - {w.description}" for w in ws[u]]
            embed.add_field(name=self.bot.get_user(u), value="\n".join(warns), inline=False)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        s = db.Session()
        for w in s.query(db.Warn).filter(db.Warn.guild == guild.id).all():
            s.delete(w)
        s.commit()
        s.close()


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Warn(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Warn")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
