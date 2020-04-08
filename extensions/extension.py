from discord.ext import commands
from discord.ext.commands.errors import CommandNotFound
from discord import Embed
from bot_bde.check import is_owner, NotOwner
from bot_bde.logger import logger


extension_name = "extension"
logger = logger.getChild(extension_name)


class Extension(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group("extension", pass_context=True)
    @commands.check(is_owner)
    async def extension(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            embed = Embed(title="Extensions")
            for extension in self.bot.extensions:
                embed.add_field(name=extension, value="Loaded", inline=False)
            await ctx.send(embed=embed)

    @extension.group("load", pass_context=True)
    @commands.check(is_owner)
    async def extension_load(self, ctx: commands.Context, name: str):
        try:
            self.bot.load_extension(name)
        except Extension as e:
            await ctx.message.add_reaction("\u26a0")
        else:
            await ctx.message.add_reaction("\U0001f44d")

    @extension.group("unload", pass_context=True)
    @commands.check(is_owner)
    async def extension_unload(self, ctx: commands.Context, name: str):
        try:
            self.bot.unload_extension(name)
        except Extension as e:
            await ctx.message.add_reaction("\u26a0")
        else:
            await ctx.message.add_reaction("\U0001f44d")

    @extension.group("reload", pass_context=True)
    @commands.check(is_owner)
    async def extension_reload(self, ctx: commands.Context, name: str):
        try:
            self.bot.unload_extension(name)
            self.bot.load_extension(name)
        except Extension as e:
            await ctx.message.add_reaction("\u26a0")
        else:
            await ctx.message.add_reaction("\U0001f44d")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, NotOwner):
            await ctx.message.add_reaction("\u274C")
        elif isinstance(error, CommandNotFound):
            await ctx.message.add_reaction("\u2753")
        else:
            await ctx.send("An error occurred !")
            raise error


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Extension(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Extension")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
