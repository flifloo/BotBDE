import re
from datetime import datetime, timezone

import ics
import requests
from discord import Embed
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands import CommandNotFound, BadArgument, MissingRequiredArgument

from bot_bde import db
from bot_bde.logger import logger

extension_name = "calendar"
logger = logger.getChild(extension_name)
url_re = re.compile(r"http:\/\/adelb\.univ-lyon1\.fr\/jsp\/custom\/modules\/plannings\/anonymous_cal\.jsp\?resources="
                    r"([0-9]+)&projectId=([0-9]+)")


class Calendar(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group("calendar", pass_context=True)
    async def calendar(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.calendar_help)

    @calendar.group("help", pass_context=True)
    async def calendar_help(self, ctx: commands.Context):
        embed = Embed(title="Calendar help")
        embed.add_field(name="calendar define <name> <url>", value="Define a calendar", inline=False)
        embed.add_field(name="calendar list", value="List all server calendar", inline=False)
        embed.add_field(name="calendar remove <name>", value="Remove a server calendar", inline=False)
        embed.add_field(name="calendar day [date]", value="show the current day or the given day", inline=False)
        embed.add_field(name="calendar week [date]", value="Show the week or the given week", inline=False)
        await ctx.send(embed=embed)

    @calendar.group("define", pass_context=True)
    async def calendar_define(self, ctx: commands.Context, name: str, url: str):
        try:
            ics.Calendar(requests.get(url).text)
        except Exception:
            raise BadArgument()
        m = url_re.findall(url)
        if not m:
            raise BadArgument()

        s = db.Session()
        if s.query(db.Calendar).filter(db.Calendar.server == ctx.guild.id).filter(db.Calendar.name == name).first():
            s.close()
            raise BadArgument()
        s.add(db.Calendar(name, int(m[0][0]), int(m[0][1]), ctx.guild.id))
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @calendar.group("list", pass_context=True)
    async def calendar_list(self, ctx: commands.Context):
        embed = Embed(title="Calendar list")
        s = db.Session()
        for c in s.query(db.Calendar).filter(db.Calendar.server == ctx.guild.id).all():
            embed.add_field(name=c.name, value=f"resources: {c.resources} | project id: {c.project_id}", inline=False)
        s.close()
        await ctx.send(embed=embed)

    @calendar.group("remove", pass_context=True)
    async def calendar_remove(self, ctx: commands.Context, name: str = None):
        if name is None:
            await ctx.invoke(self.calendar_list)
        else:
            s = db.Session()
            c = s.query(db.Calendar).filter(db.Calendar.server == ctx.guild.id).filter(db.Calendar.name == name).first()
            if c:
                s.delete(c)
                s.commit()
                s.close()
                await ctx.message.add_reaction("\U0001f44d")
            else:
                s.close()
                raise BadArgument()

    @calendar.group("day", pass_context=True)
    async def calendar_day(self, ctx: commands.Context, name: str, day: str = None):
        s = db.Session()
        c: db.Calendar = s.query(db.Calendar).filter(db.Calendar.server == ctx.guild.id).filter(db.Calendar.name == name).first()
        if not c:
            raise BadArgument()
        if day is None:
            date = datetime.now()
        else:
            try:
                date = datetime.strptime(day, "%d/%m/%Y")
            except ValueError:
                raise BadArgument()
        embed = Embed(title=f"Day calendar: {c.name}", description=date.strftime("%d/%m/%Y"))
        for e in c.events(date, date):
            embed.add_field(name=f"{e.begin.strftime('%M:%H')} - {e.end.strftime('%M:%H')}",
                            value=f"{e.name} | {e.location} - {e.organizer}", inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if ctx.invoked_with == extension_name or \
                (ctx.command.root_parent and ctx.command.root_parent.name == extension_name):
            if isinstance(error, CommandNotFound) \
                    or isinstance(error, BadArgument) \
                    or isinstance(error, MissingRequiredArgument):
                await ctx.message.add_reaction("\u2753")
                await ctx.message.delete(delay=30)
            else:
                await ctx.send("An error occurred !")
                raise error


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Calendar(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Calendar")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
