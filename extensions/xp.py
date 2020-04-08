from discord.ext import commands
from discord import Embed, Message, User
from threading import RLock
from shelve import open
from datetime import timedelta
from re import compile

from bot_bde.logger import logger


extension_name = "xp"
logger = logger.getChild(extension_name)

url_re = compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
XP = {"message": 2,
      "image": 15,
      "file": 20,
      "link": 10}
LEVEL_RATIO = 350


class Xp(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lock = RLock()

    @commands.group("xp", pass_context=True)
    @commands.guild_only()
    async def xp(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            player = None
            with self.lock:
                with open("xp", writeback=True) as data:
                    if str(ctx.author.id) in data:
                        player = data[str(ctx.author.id)]
            embed = Embed(title="Current stats")
            embed.add_field(name="level", value=player["level"])
            embed.add_field(name="xp", value=player["xp"])
            embed.add_field(name="message", value=player["message"])
            embed.add_field(name="image", value=player["image"])
            embed.add_field(name="file", value=player["file"])
            embed.add_field(name="link", value=player["link"])
            await ctx.send(embed=embed)

    @xp.group("help", pass_context=True)
    @commands.guild_only()
    async def xp_help(self, ctx: commands.Context):
        embed = Embed(title="Xp help")
        embed.add_field(name="xp", value="Show your current cp", inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if not message.author.bot:
            with self.lock:
                with open("xp", writeback=True) as data:
                    can_xp = False
                    if not str(message.author.id) in data:
                        can_xp = True
                        data[str(message.author.id)] = {"xp": 0,
                                                        "level": 0,
                                                        "message": 0,
                                                        "image": 0,
                                                        "file": 0,
                                                        "link": 0,
                                                        "last_message": message.created_at}
                    if message.created_at - data[str(message.author.id)]["last_message"] >= timedelta(minutes=2):
                        can_xp = True
                    data[str(message.author.id)]["message"] += 1
                    if can_xp:
                        data[str(message.author.id)]["xp"] += XP["message"]*len(message.content)
                    if url_re.match(message.content):
                        data[str(message.author.id)]["link"] += 1
                        if can_xp:
                            data[str(message.author.id)]["xp"] += XP["link"]
                    if message.attachments:
                        for a in message.attachments:
                            if a.width is not None:
                                data[str(message.author.id)]["image"] += 1
                                if can_xp:
                                    data[str(message.author.id)]["xp"] += XP["image"]
                            else:
                                data[str(message.author.id)]["file"] += 1
                                if can_xp:
                                    data[str(message.author.id)]["xp"] += XP["file"]
                    data[str(message.author.id)]["last_message"] = message.created_at
                    await self.level_up(message, data)

    async def level_up(self, message: Message, data):
        level_cap = data[str(message.author.id)]["level"] + 1 * LEVEL_RATIO
        if data[str(message.author.id)]["xp"] >= level_cap:
            data[str(message.author.id)]["xp"] = data[str(message.author.id)]["xp"] - level_cap
            data[str(message.author.id)]["level"] += 1
            embed = Embed(title="Level ! \U0001F389")
            embed.add_field(name="You gain one level !",
                            value=f"You reach level {data[str(message.author.id)]['level']}")
            await message.channel.send(embed=embed)


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Xp(bot))
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
