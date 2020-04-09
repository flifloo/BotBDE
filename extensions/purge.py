from asyncio import sleep

from discord.ext import commands
from discord import Embed, RawReactionActionEvent
from discord.ext.commands import CommandNotFound

from bot_bde.logger import logger


extension_name = "purge"
logger = logger.getChild(extension_name)


class Purge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.purges = {}

    @commands.group("purge", pass_context=True)
    @commands.guild_only()
    async def purge(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            if ctx.message.channel.permissions_for(ctx.author).manage_messages:
                self.purges[ctx.message.author.id] = ctx.message
                await ctx.message.add_reaction("\U0001f44d")

                await sleep(2*60)
                try:
                    if self.purges[ctx.message.author.id] == ctx.message:
                        await ctx.message.clear_reactions()
                        del self.purges[ctx.message.author.id]
                except:
                    pass
            else:
                await ctx.message.add_reaction("\u274C")

    @purge.group("help", pass_context=True)
    @commands.guild_only()
    async def purge_help(self, ctx: commands.Context):
        embed = Embed(title="Purge help")
        embed.add_field(name="purge", value="Purge all message delimited by the command to your next reaction",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        user = self.bot.get_user(payload.user_id)
        message = await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id)\
            .fetch_message(payload.message_id)
        if user.id in self.purges:
            if message.channel == self.purges[user.id].channel:
                async with message.channel.typing():
                    await message.channel.purge(before=self.purges[user.id], after=message,
                                                         limit=None)
                    await self.purges[user.id].delete()
                    await message.delete()
                    del self.purges[user.id]

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if ctx.invoked_with == extension_name or \
                (ctx.command.root_parent is not None and ctx.command.root_parent.name == extension_name):
            if isinstance(error, CommandNotFound):
                await ctx.message.add_reaction("\u2753")
            else:
                await ctx.send("An error occurred !")
                raise error


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Purge(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Speak")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
