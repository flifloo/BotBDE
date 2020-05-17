from discord.ext import commands
from discord import Embed, TextChannel, VoiceChannel
from discord.abc import GuildChannel
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, CheckFailure, BadArgument

from bot_bde.logger import logger

extension_name = "chan"
logger = logger.getChild(extension_name)


def check_editable_chan():
    async def predicate(ctx: commands.Context):
        if len(ctx.message.channel_mentions) == 0:
            return False
        elif len(ctx.message.channel_mentions) > 1:
            return False
        elif len(ctx.message.role_mentions) == 0 and len(ctx.message.mentions) == 0:
            return False
        else:
            return True

    return commands.check(predicate)


def check_permissions():
    async def predicate(ctx: commands.Context):
        if len(ctx.message.channel_mentions) == 1:
            return ctx.message.channel_mentions[0].permissions_for(ctx.author).manage_channels
        else:
            return ctx.author.guild_permissions.manage_channels

    return commands.check(predicate)


def chan_permissions(chan: GuildChannel, allow: bool):
    if type(chan) == TextChannel:
        return dict(read_messages=allow, send_messages=allow)
    elif type(chan) == VoiceChannel:
        return dict(connect=allow, speak=allow)
    else:
        raise BadArgument("Chan type Invalid")


class Chan(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.polls = {}

    @commands.group("chan", pass_context=True)
    @commands.guild_only()
    async def chan(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.chan_help)

    @chan.group("create", pass_context=True)
    @commands.guild_only()
    @check_permissions()
    async def chan_create(self, ctx: commands.Context, name: str):
        chan: TextChannel = await ctx.guild.create_text_channel(name)
        if len(ctx.message.role_mentions) != 0 or len(ctx.message.mentions) != 0:
            await chan.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False)
            for r in ctx.message.role_mentions:
                await chan.set_permissions(r, read_messages=True, send_messages=True)
            for m in ctx.message.mentions:
                await chan.set_permissions(m, read_messages=True, send_messages=True)

    @chan.group("deny", pass_context=True)
    @commands.guild_only()
    @check_editable_chan()
    @check_permissions()
    async def chan_deny(self, ctx: commands.Context):
        for r in ctx.message.role_mentions:
            await ctx.message.channel_mentions[0].set_permissions(r,
                                                                  **chan_permissions(ctx.message.channel_mentions[0],
                                                                                     False))
        for m in ctx.message.mentions:
            await ctx.message.channel_mentions[0].set_permissions(m,
                                                                  **chan_permissions(ctx.message.channel_mentions[0],
                                                                                     False))

    @chan.group("allow", pass_context=True)
    @commands.guild_only()
    @check_editable_chan()
    @check_permissions()
    async def allow_deny(self, ctx: commands.Context):
        for r in ctx.message.role_mentions:
            await ctx.message.channel_mentions[0].set_permissions(r,
                                                                  **chan_permissions(ctx.message.channel_mentions[0],
                                                                                     True))
        for m in ctx.message.mentions:
            await ctx.message.channel_mentions[0].set_permissions(m,
                                                                  **chan_permissions(ctx.message.channel_mentions[0],
                                                                                     True))

    @chan.group("help", pass_context=True)
    @commands.guild_only()
    async def chan_help(self, ctx: commands.Context):
        embed = Embed(title="chan help")
        embed.add_field(name="chan create <name> [@role|@user]",
                        value="Create a new chan, the roles and/or users mentioned will be the only one permitted to "
                              "read and write in the chan",
                        inline=False)
        embed.add_field(name="chan deny <@chan> <@role|@user>",
                        value="Edit chan permission, the roles and/or users mentioned will be deny for read and write "
                              "in the chan",
                        inline=False)
        embed.add_field(name="chan allow <@chan> <@role|@user>",
                        value="Edit chan permission, the roles and/or users mentioned will be allow to read and write "
                              "in the chan",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if ctx.invoked_with == extension_name or \
                (ctx.command.root_parent is not None and ctx.command.root_parent.name == extension_name):
            if isinstance(error, CommandNotFound):
                await ctx.message.add_reaction("\u2753")
                await ctx.message.delete(delay=30)
            if isinstance(error, MissingRequiredArgument) or isinstance(error, CheckFailure):
                await ctx.message.add_reaction("\u274C")
                await ctx.message.delete(delay=30)
            else:
                await ctx.send("An error occurred !")
                raise error


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Chan(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Chan")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
