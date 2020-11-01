from urllib.parse import urlencode

from discord import Embed
from discord.ext import commands

from administrator.logger import logger


extension_name = "TeX"


class TeX(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.polls = {}

    def description(self):
        return "Render TeX formula"

    @commands.group("tex", pass_context=True)
    async def tex(self, ctx: commands.Context):
        if ctx.message.content.count("`") == 2:
            start = ctx.message.content.find("`")
            end = ctx.message.content.find("`", start+1)
            command = ctx.message.content[start+1:end]
            await ctx.send(f"https://chart.apis.google.com/chart?cht=tx&chs=40&{urlencode({'chl': command})}")
        elif ctx.invoked_subcommand is None:
            await ctx.invoke(self.tex_help)

    @tex.group("help", pass_context=True)
    async def tex_help(self, ctx: commands.Context):
        embed = Embed(title="TeX help")
        embed.add_field(name="tex \`formula\`", value="Render a TeX formula", inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(TeX(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("TeX")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
