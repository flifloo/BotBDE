from discord.ext import commands
from discord import Embed, TextChannel
from discord.ext.commands import CommandNotFound, MissingRequiredArgument

from bot_bde.logger import logger


extension_name = "chan"
logger = logger.getChild(extension_name)
REACTIONS = []
for i in range(10):
    REACTIONS.append(str(i)+"\ufe0f\u20E3")
REACTIONS.append("\U0001F51F")


class Chan(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.polls = {}

    @commands.group("chan", pass_context=True)
    @commands.guild_only()
    async def chan(self, ctx: commands.Context, name: str):
        if name == "help":
            await ctx.invoke(self.chan_help)
        else:
            chan: TextChannel = await ctx.guild.create_text_channel(name)
            if len(ctx.message.role_mentions) != 0:
                await chan.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False)
                for r in ctx.message.role_mentions:
                    await chan.set_permissions(r, read_messages=True, send_messages=True)

    @chan.group("help", pass_context=True)
    @commands.guild_only()
    async def chan_help(self, ctx: commands.Context):
        embed = Embed(title="chan help")
        embed.add_field(name="chan <name> [@role]",
                        value="Create a new chan, the roles mentioned will be the only one permitted to read and write "
                              "in the chan\n",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if ctx.invoked_with == extension_name or \
                (ctx.command.root_parent is not None and ctx.command.root_parent.name == extension_name):
            if isinstance(error, CommandNotFound):
                await ctx.message.add_reaction("\u2753")
                await ctx.message.delete(delay=30)
            if isinstance(error, MissingRequiredArgument):
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
