import re

from discord import Embed, Member
from discord.ext import commands
from discord.ext.commands import BadArgument

from administrator.logger import logger


extension_name = "PCP"
logger = logger.getChild(extension_name)
group_re = re.compile(r"(G[0-9]S[0-9]|ASPE|LP DEVOPS|LP ESSIR|LP SID)")


class PCP(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.polls = {}

    def description(self):
        return "PCP Univ Lyon 1"

    @commands.group("pcp", pass_context=True)
    @commands.guild_only()
    async def pcp(self, ctx: commands.Context):
        group = ctx.message.content.replace(f"{ctx.prefix}{ctx.command} ", "").upper()
        if group and group_re.fullmatch(group):
            role = next(filter(lambda r: r.name.upper() == group, ctx.guild.roles), None)

            if not role:
                raise BadArgument()

            roles = list(filter(lambda r: group_re.fullmatch(r.name.upper()) or r.name == "nouveau venu", ctx.author.roles))
            if role.name in map(lambda r: r.name, roles):
                raise BadArgument()
            elif roles:
                await ctx.author.remove_roles(*roles)

            await ctx.author.add_roles(role)
            await ctx.message.add_reaction("\U0001f44d")
            return
        elif ctx.invoked_subcommand is None:
            await ctx.invoke(self.pcp_help)

    @pcp.group("help", pass_context=True)
    @commands.guild_only()
    async def pcp_help(self, ctx: commands.Context):
        embed = Embed(title="PCP help")
        embed.add_field(name="pcp <group>", value="Join your group", inline=False)
        if await self.pcp_group.can_run(ctx):
            embed.add_field(name="pcp group", value="Manage PCP group", inline=False)
        await ctx.send(embed=embed)

    @pcp.group("group", pass_context=True)
    @commands.has_permissions(administrator=True)
    async def pcp_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.pcp_group_help)

    @pcp_group.group("help", pass_context=True)
    async def pcp_group_help(self, ctx: commands.Context):
        embed = Embed(title="PCP group help")
        embed.add_field(name="pcp group subject", value="Manage subjects for group", inline=False)
        await ctx.send(embed=embed)

    @pcp_group.group("fix_vocal", pass_context=True)
    async def pcp_group_fix_vocal(self, ctx: commands.Context):
        for cat in filter(lambda c: group_re.fullmatch(c.name.upper()), ctx.guild.categories):
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


    @pcp_group.group("subject", pass_context=True)
    async def pcp_group_subject(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.pcp_group_subject_help)

    @pcp_group_subject.group("help", pass_context=True)
    async def pcp_group_subject_help(self, ctx: commands.Context):
        embed = Embed(title="PCP group subject help")
        embed.add_field(name="pcp group subject add <name> <@group> [@teacher]", value="Add a subject to a group",
                        inline=False)
        embed.add_field(name="pcp group subject remove <name> <@group>", value="Remove a subject to a group",
                        inline=False)
        await ctx.send(embed=embed)

    @pcp_group_subject.group("add", pass_context=True)
    async def pcp_group_subject_add(self, ctx: commands.Context, name: str):
        if len(ctx.message.role_mentions) != 1:
            raise BadArgument()
        if len(ctx.message.mentions) > 1:
            raise BadArgument()
        elif ctx.message.mentions and\
                not next(filter(lambda r: r.name == "professeurs", ctx.message.mentions[0].roles), None):
            raise BadArgument()

        cat = next(filter(lambda c: c.name.upper() == ctx.message.role_mentions[0].name.upper(), ctx.guild.categories), None)
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
        for n in names:
            await ctx.invoke(self.pcp_group_subject_add, n)

    @pcp_group_subject.group("remove", pass_context=True)
    async def pcp_group_subject_remove(self, ctx: commands.Context, name: str):
        if len(ctx.message.role_mentions) != 1:
            raise BadArgument()

        cat = next(filter(lambda c: c.name.upper() == ctx.message.role_mentions[0].name.upper(), ctx.guild.categories), None)
        if not cat:
            raise BadArgument()

        chan = next(filter(lambda c: c.name.upper() == name.upper(), cat.text_channels), None)
        if not cat:
            raise BadArgument()

        await chan.delete()

        await ctx.message.add_reaction("\U0001f44d")

    @pcp.group("eval", pass_context=True)
    @commands.is_owner()
    async def eval(self, ctx: commands.Context):
        start = ctx.message.content.find("```")
        end = ctx.message.content.find("```", start+3)
        command = ctx.message.content[start+3:end]
        try:
            exec("async def __ex(self, ctx):\n" + command.replace("\n", "\n    "))
            await locals()["__ex"](self, ctx)
        except Exception as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")

    @pcp.group("test", pass_context=True)
    async def test(self, ctx: commands.Context):
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
