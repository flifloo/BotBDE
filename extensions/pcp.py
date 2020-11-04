import re

from discord import Embed, Member
from discord.ext import commands
from discord.ext.commands import BadArgument, MissingPermissions

import db
from administrator.logger import logger


extension_name = "PCP"
logger = logger.getChild(extension_name)
msg_url_re = re.compile(r"^https://.*discord.*\.com/channels/[0-9]+/([0-9+]+)/([0-9]+)$")
role_mention_re = re.compile(r"^<@&[0-9]+>$")
user_mention_re = re.compile(r"^<@![0-9]+>$")


class PCP(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "PCP Univ Lyon 1"

    @commands.group("pcp", pass_context=True)
    @commands.guild_only()
    async def pcp(self, ctx: commands.Context):
        group = ctx.message.content.replace(f"{ctx.prefix}{ctx.command} ", "").upper()
        if group:
            s = db.Session()
            p = s.query(db.PCP).get(ctx.guild.id)
            s.close()
            if p and re.fullmatch(p.roles_re, group):
                await ctx.message.add_reaction("\U000023f3")
                role = next(filter(lambda r: r.name.upper() == group, ctx.guild.roles), None)

                def roles() -> list:
                    return list(filter(
                        lambda r: re.fullmatch(p.roles_re, r.name.upper()) or
                        (p.start_role_re and re.fullmatch(p.start_role_re, r.name.upper())),
                        ctx.author.roles
                    ))

                if not role or role.name in map(lambda r: r.name, roles()):
                    await ctx.message.remove_reaction("\U000023f3", self.bot.user)
                    raise BadArgument()

                while roles():
                    await ctx.author.remove_roles(*roles())

                while role not in ctx.author.roles:
                    await ctx.author.add_roles(role)
                await ctx.message.remove_reaction("\U000023f3", self.bot.user)
                await ctx.message.add_reaction("\U0001f44d")
                return

        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.pcp_help)

    @pcp.group("help", pass_context=True)
    async def pcp_help(self, ctx: commands.Context):
        embed = Embed(title="PCP help")
        s = db.Session()
        p = s.query(db.PCP).get(ctx.guild.id)
        s.close()
        if p:
            embed.add_field(name="pcp <group>", value="Join your group", inline=False)
        if await self.pcp_group.can_run(ctx):
            embed.add_field(name="pcp group", value="Manage PCP group", inline=False)
        if not embed.fields:
            raise MissingPermissions(None)
        await ctx.send(embed=embed)

    @pcp.group("pin", pass_context=True)
    async def pcp_pin(self, ctx: commands.Context, url: str):
        r = msg_url_re.fullmatch(url)
        if not r:
            raise BadArgument()
        r = r.groups()

        c = ctx.guild.get_channel(int(r[0]))
        if not c:
            raise BadArgument()

        m = await c.fetch_message(int(r[1]))
        if not m:
            raise BadArgument()

        await m.pin()

        await ctx.send(f"{ctx.author.mention} pinned a message")

    @pcp.group("group", pass_context=True)
    @commands.has_permissions(administrator=True)
    async def pcp_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.pcp_group_help)

    @pcp_group.group("help", pass_context=True)
    async def pcp_group_help(self, ctx: commands.Context):
        embed = Embed(title="PCP group help")
        embed.add_field(name="pcp group set <role Regex> [Welcome role Regex]",
                        value="Set regex for group role", inline=False)
        embed.add_field(name="pcp group unset", value="Unset regex for group role", inline=False)
        embed.add_field(name="pcp group subject", value="Manage subjects for group", inline=False)
        embed.add_field(name="pcp group fix_vocal",
                        value="Check all text channel permissions to reapply vocal permissions", inline=False)
        await ctx.send(embed=embed)

    @pcp_group.group("fix_vocal", pass_context=True)
    async def pcp_group_fix_vocal(self, ctx: commands.Context):
        s = db.Session()
        p = s.query(db.PCP).get(ctx.guild.id)
        s.close()
        if not p:
            raise BadArgument()

        for cat in filter(lambda c: re.fullmatch(p.roles_re, c.name.upper()), ctx.guild.categories):
            await ctx.send(f"{cat.name}...")
            teachers = []
            for t in cat.text_channels:
                for p in t.overwrites:
                    if isinstance(p, Member):
                        teachers.append(p)
            voc = next(filter(lambda c: c.name == "vocal-1", cat.voice_channels), None)
            for t in teachers:
                await voc.set_permissions(t, view_channel=True)
            await ctx.send(f"{cat.name} done")
        await ctx.message.add_reaction("\U0001f44d")

    @pcp_group.group("set", pass_context=True)
    async def pcp_group_set(self, ctx: commands.Context, roles_re: str, start_role_re: str = None):
        s = db.Session()
        p = s.query(db.PCP).get(ctx.guild.id)
        if p:
            p.roles_re = roles_re.upper()
            p.start_role_re = start_role_re.upper() if start_role_re else None
        else:
            p = db.PCP(ctx.guild.id, roles_re.upper(), start_role_re.upper() if start_role_re else None)
        s.add(p)
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @pcp_group.group("unset", pass_context=True)
    async def pcp_group_unset(self, ctx: commands.Context):
        s = db.Session()
        p = s.query(db.PCP).get(ctx.guild.id)
        if not p:
            s.close()
            raise BadArgument()
        s.delete(p)
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @pcp_group.group("subject", pass_context=True)
    async def pcp_group_subject(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.pcp_group_subject_help)

    @pcp_group_subject.group("help", pass_context=True)
    async def pcp_group_subject_help(self, ctx: commands.Context):
        embed = Embed(title="PCP group subject help")
        embed.add_field(name="pcp group subject add <name> <@group> [@teacher]", value="Add a subject to a group",
                        inline=False)
        embed.add_field(name="pcp group subject bulk <@group> [subject1] [subject2] ...", value="Bulk subject add",
                        inline=False)
        embed.add_field(name="pcp group subject remove <name> <@group>", value="Remove a subject to a group",
                        inline=False)
        await ctx.send(embed=embed)

    @pcp_group_subject.group("add", pass_context=True)
    async def pcp_group_subject_add(self, ctx: commands.Context, name: str, group: str, teacher: str = None):
        if not role_mention_re.fullmatch(group):
            raise BadArgument()
        if teacher and not user_mention_re.fullmatch(teacher):
            raise BadArgument()
        elif teacher and\
                not next(filter(lambda r: r.name == "professeurs", ctx.message.mentions[0].roles), None):
            raise BadArgument()

        cat = next(filter(lambda c: c.name.upper() == ctx.message.role_mentions[0].name.upper(),
                          ctx.guild.categories), None)
        if not cat:
            raise BadArgument()

        chan = next(filter(lambda c: c.name.upper() == name.upper(), cat.text_channels), None)
        if not chan:
            chan = await cat.create_text_channel(name)
        voc = next(filter(lambda c: c.name == "vocal-1", cat.voice_channels), None)
        if not voc:
            voc = await cat.create_voice_channel("vocal-1")
        if ctx.message.mentions:
            await chan.set_permissions(ctx.message.mentions[0], read_messages=True)
            await voc.set_permissions(ctx.message.mentions[0], view_channel=True)

        await ctx.message.add_reaction("\U0001f44d")

    @pcp_group_subject.group("bulk", pass_context=True)
    async def pcp_group_subject_bulk(self, ctx: commands.Context, mention, *names):
        if not role_mention_re.fullmatch(mention):
            raise BadArgument()
        for n in names:
            await ctx.invoke(self.pcp_group_subject_add, n, mention)

    @pcp_group_subject.group("remove", pass_context=True)
    async def pcp_group_subject_remove(self, ctx: commands.Context, name: str, group: str):
        if not role_mention_re.fullmatch(group):
            raise BadArgument()

        cat = next(filter(lambda c: c.name.upper() == ctx.message.role_mentions[0].name.upper(),
                          ctx.guild.categories), None)
        if not cat:
            raise BadArgument()

        chan = next(filter(lambda c: c.name.upper() == name.upper(), cat.text_channels), None)
        if not chan:
            raise BadArgument()

        await chan.delete()

        await ctx.message.add_reaction("\U0001f44d")


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(PCP(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("PCP")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
