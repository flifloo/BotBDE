from discord import Embed, Forbidden, Member, Guild
from discord.ext import commands
from discord.ext.commands import BadArgument

from administrator import db
from administrator.logger import logger
from administrator.utils import time_pars

extension_name = "warn"
logger = logger.getChild(extension_name)


class Warn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "Send warning to user and make custom action after a number of warn"

    @staticmethod
    async def check_warn(ctx: commands.Context, target: Member):
        s = db.Session()
        c = s.query(db.Warn).filter(db.Warn.guild == ctx.guild.id, db.Warn.user == target.id).count()
        a = s.query(db.WarnAction).filter(db.WarnAction.guild == ctx.guild.id, db.WarnAction.count == c).first()
        if a:
            reason = f"Action after {c} warns"
            if a.action == "kick":
                await target.kick(reason=reason)
            elif a.action == "ban":
                await target.ban(reason=reason)
            elif a.action == "mute":
                pass  # Integration with upcoming ban & mute extension

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
        embed.add_field(name="action <count> <action>", value="Set an action for a count of warn\n"
                                                              "Actions: `mute<time>`, `kick`, `ban[time]`, `nothing`\n"
                                                              "Time: `?D?H?M?S`\n"
                                                              "Example: `action 1 mute1H` to mute someone for one hour "
                                                              "after only one war\n"
                                                              "or `action 3 ban3D` to ban someone for one day after 3 "
                                                              "warns", inline=False)
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
        await self.check_warn(ctx, target)

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
            warns = [f"{self.bot.get_user(w.author).mention} - {w.date.strftime('%d/%m/%Y %H:%M')}```{w.description}```"
                     for w in ws[u]]
            embed.add_field(name=self.bot.get_user(u), value="\n".join(warns), inline=False)

        await ctx.send(embed=embed)

    @warn.group("action", pass_context=True)
    async def warn_action(self, ctx: commands.Context, count: int, action: str):
        if count <= 0 or\
                (action not in ["kick", "nothing"] and not action.startswith("mute") and not action.startswith("ban")):
            raise BadArgument()

        s = db.Session()
        a = s.query(db.WarnAction).filter(db.WarnAction.guild == ctx.guild.id, db.WarnAction.count == count).first()

        if action == "nothing":
            if a:
                s.delete(a)
            else:
                raise BadArgument()
        else:
            time = None
            if action.startswith("mute"):
                time = time_pars(action.replace("mute", "")).total_seconds()
                action = "mute"
            elif action.startswith("ban"):
                if action[3:]:
                    time = time_pars(action.replace("ban", "")).total_seconds()
                    action = "ban"
            if a:
                a.action = action
                a.duration = time
            else:
                s.add(db.WarnAction(ctx.guild.id, count, action, time))

        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        s = db.Session()
        for w in s.query(db.Warn).filter(db.Warn.guild == guild.id).all():
            s.delete(w)
        for a in s.query(db.WarnAction).filter(db.WarnAction.guild == guild.id).all():
            s.delete(a)
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
