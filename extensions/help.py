from discord import Embed
from discord.ext import commands
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, BadArgument, MissingPermissions, \
    NoPrivateMessage, CommandError, NotOwner

from administrator import config
from administrator.check import ExtensionDisabled
from administrator.logger import logger


extension_name = "help"
logger = logger.getChild(extension_name)


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "Give help and command list"

    @commands.command("help", pass_context=True)
    async def help(self, ctx: commands.Context):
        embed = Embed(title="Help")

        for c in filter(lambda x: x != "Help", self.bot.cogs):
            cog = self.bot.cogs[c]
            try:
                if await getattr(cog, c.lower()).can_run(ctx):
                    embed.add_field(name=c,
                                    value=cog.description() + "\n" +
                                    f"`{config.get('prefix')}{c.lower()} help` for more information",
                                    inline=False)
            except CommandError:
                pass

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            await ctx.message.add_reaction("\u2753")
        elif isinstance(error, MissingRequiredArgument) or isinstance(error, BadArgument):
            await ctx.message.add_reaction("\u274C")
        elif isinstance(error, NotOwner) or isinstance(error, MissingPermissions)\
                or isinstance(error, NoPrivateMessage):
            await ctx.message.add_reaction("\U000026D4")
        elif isinstance(error, ExtensionDisabled):
            await ctx.message.add_reaction("\U0001F6AB")
        else:
            await ctx.send("An error occurred !")
            raise error
        await ctx.message.delete(delay=30)


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.help_command = None
        bot.add_cog(Help(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Help")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
