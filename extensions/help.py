from discord.ext import commands
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, BadArgument, MissingPermissions

from administrator.logger import logger
from administrator.check import NotOwner


extension_name = "help"
logger = logger.getChild(extension_name)


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.purges = {}

    @commands.command("help", pass_context=True)
    async def help(self, ctx: commands.Context):
        await ctx.send("HALP !")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            await ctx.message.add_reaction("\u2753")
        elif isinstance(error, MissingRequiredArgument) or isinstance(error, BadArgument):
            await ctx.message.add_reaction("\u274C")
        elif isinstance(error, NotOwner) or isinstance(error, MissingPermissions):
            await ctx.message.add_reaction("\u274C")
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
