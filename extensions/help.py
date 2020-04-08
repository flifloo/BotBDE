from discord.ext import commands
from bot_bde.logger import logger


extension_name = "help"
logger = logger.getChild(extension_name)


@commands.command("help")
async def help_cmd(ctx):
    await ctx.send("Help !")


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.help_command = None
        bot.add_command(help_cmd)
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_command("help")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
