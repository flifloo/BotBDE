import re
from datetime import datetime, timedelta
from operator import xor

import ics
import requests
from discord import Embed, DMChannel, TextChannel
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands import CommandNotFound, BadArgument, MissingRequiredArgument, MissingPermissions

from bot_bde import db
from bot_bde.logger import logger


extension_name = "calendar"
logger = logger.getChild(extension_name)
url_re = re.compile(r"http:\/\/adelb\.univ-lyon1\.fr\/jsp\/custom\/modules\/plannings\/anonymous_cal\.jsp\?resources="
                    r"([0-9]+)&projectId=([0-9]+)")


def query_calendar(name: str, guild: int) -> db.Calendar:
    s = db.Session()
    c: db.Calendar = s.query(db.Calendar).filter(db.Calendar.server == guild).filter(db.Calendar.name == name).first()
    s.close()
    if not c:
        raise BadArgument()
    return c


async def get_one_text_channel(ctx: commands.Context):
    if ctx.message.channel_mentions:
        if not ctx.channel.permissions_for(ctx.author).manage_channels:
            raise MissingPermissions(["manage_channels"])
        elif len(ctx.message.channel_mentions) > 1:
            raise BadArgument()
        else:
            m = ctx.message.channel_mentions[0].id
    else:
        if not ctx.author.dm_channel:
            await ctx.author.create_dm()
        m = ctx.author.dm_channel.id
    return m


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
        embed.add_field(name="calendar day <name> [date]", value="show the current day or the given day", inline=False)
        embed.add_field(name="calendar week <name> [date]", value="Show the week or the given week", inline=False)
        embed.add_field(name="calendar notify",
                        value="Command group to manage calendar notifications", inline=False)
        await ctx.send(embed=embed)

    @calendar.group("define", pass_context=True)
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
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
    @commands.guild_only()
    async def calendar_list(self, ctx: commands.Context):
        embed = Embed(title="Calendar list")
        s = db.Session()
        for c in s.query(db.Calendar).filter(db.Calendar.server == ctx.guild.id).all():
            embed.add_field(name=c.name, value=f"resources: {c.resources} | project id: {c.project_id}", inline=False)
        s.close()
        await ctx.send(embed=embed)

    @calendar.group("remove", pass_context=True)
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
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
    @commands.guild_only()
    async def calendar_day(self, ctx: commands.Context, name: str, day: str = None):
        c = query_calendar(name, ctx.guild.id)
        if day is None:
            date = datetime.now().date()
        else:
            try:
                date = datetime.strptime(day, "%d/%m/%Y").date()
            except ValueError:
                raise BadArgument()
        embed = Embed(title=f"Day calendar: {c.name}", description=date.strftime("%d/%m/%Y"))
        for e in c.events(date, date):
            embed.add_field(name=f"{e.begin.strftime('%H:%M')} - {e.end.strftime('%H:%M')}",
                            value=f"{e.name} | {e.location} - {e.organizer}", inline=False)
        s = db.Session()
        if s.is_modified(c):
            s.add(c)
            s.commit()
        s.close()
        await ctx.send(embed=embed)

    @calendar.group("week", pass_context=True)
    @commands.guild_only()
    async def calendar_week(self, ctx: commands.Context, name: str, day: str = None):
        c = query_calendar(name, ctx.guild.id)
        if day is None:
            date = datetime.now().date()
        else:
            try:
                date = datetime.strptime(day, "%d/%m/%Y").date()
            except ValueError:
                raise BadArgument()
        date -= timedelta(days=date.weekday())
        embed = Embed(title=f"Week calendar: {c.name}",
                      description=f"{date.strftime('%d/%m/%Y')} - {(date + timedelta(days=4)).strftime('%d/%m/%Y')}")
        for d in range(5):
            events = []
            for e in c.events(date, date):
                events.append(f"*{e.begin.strftime('%H:%M')} - {e.end.strftime('%H:%M')}*: "
                              f"**{e.name}** | {e.location} - {e.organizer}")
            embed.add_field(name=date.strftime("%d/%m/%Y"), value="\n".join(events) or "Nothing !", inline=False)
            date = date + timedelta(days=1)
        s = db.Session()
        if s.is_modified(c):
            s.add(c)
            s.commit()
        s.close()
        await ctx.send(embed=embed)

    @calendar.group("notify", pass_context=True)
    async def calendar_notify(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.calendar_notify_help)

    @calendar_notify.group("help", pass_context=True)
    async def calendar_notify_help(self, ctx: commands.Context):
        embed = Embed(title="Calendar notify help")
        embed.add_field(name="calendar notify add <name> [#channel]",
                        value="Notify you or the giver channel of calendar events", inline=False)
        embed.add_field(name="calendar notify remove <name> [#channel]",
                        value="Remove the calendar notify of the current user or the given channel",
                        inline=False)
        embed.add_field(name="calendar notify list [name]",
                        value="List all notify of all calendar or the given one", inline=False)
        await ctx.send(embed=embed)

    @calendar_notify.group("add", pass_context=True)
    @commands.guild_only()
    async def calendar_notify_set(self, ctx: commands.Context, name: str):
        m = await get_one_text_channel(ctx)
        s = db.Session()
        c = query_calendar(name, ctx.guild.id)
        n = s.query(db.CalendarNotify).filter(db.CalendarNotify.channel == m) \
            .filter(db.CalendarNotify.calendar_id == c.id) \
            .first()
        if not n:
            s.add(db.CalendarNotify(m, c.id))
        else:
            s.close()
            raise BadArgument()
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @calendar_notify.group("remove", pass_context=True)
    @commands.guild_only()
    async def calendar_notify_remove(self, ctx: commands.Context, name: str):
        m = await get_one_text_channel(ctx)
        s = db.Session()
        c = query_calendar(name, ctx.guild.id)
        n = s.query(db.CalendarNotify).filter(db.CalendarNotify.channel == m) \
            .filter(db.CalendarNotify.calendar_id == c.id) \
            .first()
        if n:
            s.delete(n)
        else:
            s.close()
            raise BadArgument()
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @calendar_notify.group("list")
    @commands.guild_only()
    async def calendar_notify_list(self, ctx: commands.Context, name: str = None):
        s = db.Session()
        embed = Embed(title="Notify list")
        if name is None:
            calendars = s.query(db.Calendar).filter(db.Calendar.server == ctx.guild.id).all()
        else:
            calendars = [query_calendar(name, ctx.guild.id)]
        for c in calendars:
            notify = []
            for n in c.calendars_notify:
                ch = self.bot.get_channel(n.channel)
                if type(ch) == TextChannel:
                    notify.append(ch.mention)
                elif type(ch) == DMChannel:
                    notify.append(ch.recipient.mention)
            embed.add_field(name=c.name, value="\n".join(notify) or "Nothing here", inline=False)
        await ctx.send(embed=embed)

    @tasks.loop(minutes=1)
    async def calendar_notify_loop(self):
        s = db.Session()
        now = datetime.now().astimezone(tz=None)
        for c in s.query(db.Calendar).all():
            for e in c.events(now.date(), now.date()):
                if xor(c.last_notify.astimezone(tz=None) < e.begin - timedelta(minutes=30) <= now,
                       c.last_notify.astimezone(tz=None) < e.begin - timedelta(minutes=10) <= now):
                    self.bot.loop.create_task(c.notify(self.bot, e))
            if s.is_modified(c):
                s.add(c)
                s.commit()
        s.close()

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if ctx.invoked_with == extension_name or \
                (ctx.command.root_parent and ctx.command.root_parent.name == extension_name):
            if isinstance(error, CommandNotFound) \
                    or isinstance(error, BadArgument) \
                    or isinstance(error, MissingRequiredArgument):
                await ctx.message.add_reaction("\u2753")
                await ctx.message.delete(delay=30)
            elif isinstance(error, MissingPermissions):
                await ctx.message.add_reaction("\u274c")
                await ctx.message.delete(delay=30)
            else:
                await ctx.send("An error occurred !")
                raise error

    def cog_unload(self):
        self.calendar_notify_loop.stop()


def setup(bot):
    logger.info(f"Loading...")
    try:
        calendar = Calendar(bot)
        bot.add_cog(calendar)
        calendar.calendar_notify_loop.start()
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
