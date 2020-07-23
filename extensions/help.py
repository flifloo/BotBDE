from discord import Embed
from discord.ext import commands
from discord.ext.commands import CommandNotFound, MissingRequiredArgument, BadArgument, MissingPermissions, \
    NoPrivateMessage

from administrator import config
from administrator.logger import logger
from administrator.check import NotOwner, is_owner


extension_name = "help"
logger = logger.getChild(extension_name)


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command("help", pass_context=True)
    async def help(self, ctx: commands.Context):
        embed = Embed(title="Help")
        embed.add_field(name="Poll", value="Create poll with a simple command\n"
                                           f"`{config.get('prefix')}poll help` for more information", inline=False)
        embed.add_field(name="Reminders", value="Create reminders\n"
                                                f"`{config.get('prefix')}reminder help` for more information",
                        inline=False)
        permissions = ctx.channel.permissions_for(ctx.author)
        if permissions.manage_messages:
            embed.add_field(name="Purge", value="Purge all messages between the command and the next add reaction\n"
                                                f"`{config.get('prefix')}purge help` for more information", inline=False)
        if permissions.manage_guild:
            embed.add_field(name="Greetings", value="Setup join and leave message\n"
                                                    f"`{config.get('prefix')}greetings help` for more information",
                            inline=False)
            embed.add_field(name="Presentation", value="Give role to user who make a presentation in a dedicated "
                                                       "channel\n"
                                                       f"`{config.get('prefix')}presentation help` for more information",
                            inline=False)
        if await is_owner(ctx):
            embed.add_field(name="Extension", value="Manage bot extensions\n"
                                                    f"`{config.get('prefix')}extension help` for more information",
                            inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            await ctx.message.add_reaction("\u2753")
        elif isinstance(error, MissingRequiredArgument) or isinstance(error, BadArgument):
            await ctx.message.add_reaction("\u274C")
        elif isinstance(error, NotOwner) or isinstance(error, MissingPermissions)\
                or isinstance(error, NoPrivateMessage):
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
