import re
from datetime import datetime
from time import mktime, struct_time

from discord import Embed, Forbidden
from discord.ext import commands, tasks
from discord.ext.commands import BadArgument
from feedparser import parse

import db
from administrator.logger import logger


extension_name = "tomuss"
logger = logger.getChild(extension_name)
url_re = re.compile(r"https://tomuss\.univ-lyon1\.fr/S/[0-9]{4}/[a-zA-Z]+/rss/.+")


class Tomuss(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tomuss_loop.start()

    def description(self):
        return "PCP Univ Lyon 1"

    @commands.group("tomuss", pass_context=True)
    async def tomuss(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.tomuss_help)

    @tomuss.group("help", pass_context=True)
    async def tomuss_help(self, ctx: commands.Context):
        embed = Embed(title="Tomuss help")
        embed.add_field(name="tomuss set <url>", value="Set your tomuss RSS feed", inline=False)
        embed.add_field(name="tomuss unset", value="Unset your tomuss RSS feed", inline=False)
        await ctx.send(embed=embed)

    @tomuss.group("set", pass_context=True)
    async def tomuss_set(self, ctx: commands.Context, url: str):
        if not url_re.fullmatch(url):
            raise BadArgument()
        entries = parse(url).entries

        if not entries:
            raise BadArgument()
        last = datetime.fromtimestamp(mktime(sorted(entries, key=lambda e: e.published_parsed)[0].published_parsed))

        s = db.Session()
        t = s.query(db.Tomuss).get(ctx.author.id)
        if t:
            t.url = url
            t.last = last
        else:
            t = db.Tomuss(ctx.author.id, url, last)
        s.add(t)
        s.commit()
        s.close()

        await ctx.message.add_reaction("\U0001f44d")

    @tomuss.group("unset", pass_context=True)
    async def tomuss_unset(self, ctx: commands.Context):
        s = db.Session()
        t = s.query(db.Tomuss).get(ctx.author.id)
        if not t:
            raise BadArgument()
        s.delete(t)
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @tasks.loop(minutes=5)
    async def tomuss_loop(self):
        s = db.Session()

        for t in s.query(db.Tomuss).all():
            u = await self.bot.fetch_user(t.user_id)
            if not u:
                s.delete(t)
                s.commit()
                continue

            last = t.last.utctimetuple()
            entries = list(filter(lambda e: e.published_parsed > last,
                                  sorted(parse(t.url).entries, key=lambda e: e.published_parsed)))
            if entries:
                embed = Embed(title="Tomuss update !")
                for e in entries:
                    embed.add_field(name=e.title,
                                    value=e.summary.replace("<br />", "\n").replace("<b>", "**").replace("</b>", "**"))
                try:
                    await u.send(embed=embed)

                    t.last = datetime.fromtimestamp(mktime(entries[-1].published_parsed))
                    s.add(t)
                except Forbidden:
                    s.delete(t)
                s.commit()

        s.close()

    def cog_unload(self):
        self.tomuss_loop.stop()


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Tomuss(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Tomuss")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
