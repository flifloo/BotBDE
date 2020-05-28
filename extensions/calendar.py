import re
from datetime import datetime, timedelta

import ics
import requests
from discord import Embed, DMChannel, TextChannel
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands import CommandNotFound, BadArgument, MissingRequiredArgument

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
            date = datetime.now()
        else:
            try:
                date = datetime.strptime(day, "%d/%m/%Y")
            except ValueError:
                raise BadArgument()
        embed = Embed(title=f"Day calendar: {c.name}", description=date.strftime("%d/%m/%Y"))
        for e in c.events(date, date):
            embed.add_field(name=f"{e.begin.strftime('%H:%M')} - {e.end.strftime('%H:%M')}",
                            value=f"{e.name} | {e.location} - {e.organizer}", inline=False)
        await ctx.send(embed=embed)

    @calendar.group("week", pass_context=True)
    @commands.guild_only()
    async def calendar_week(self, ctx: commands.Context, name: str, day: str = None):
        c = query_calendar(name, ctx.guild.id)
        if day is None:
            date = datetime.now()
        else:
            try:
                date = datetime.strptime(day, "%d/%m/%Y")
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
        await ctx.send(embed=embed)

    @calendar.group("notify", pass_context=True)
    async def calendar_notify(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.calendar_notify_help)

    @calendar_notify.group("help", pass_context=True)
    async def calendar_notify_help(self, ctx: commands.Context):
        embed = Embed(title="Calendar notify help")
        embed.add_field(name="calendar notify set <name> [#channel|@user] [rm]",
                        value="Notify the current channel or the giver channel/user of calendar events\n"
                              "If you put `rm` at the end the notification will be delete", inline=False)
        await ctx.send(embed=embed)

    @calendar_notify.group("set", pass_context=True)
    @commands.guild_only()
    async def calendar_notify_set(self, ctx: commands.Context, name: str, action: str = None):
        if ctx.message.channel_mentions and ctx.message.mentions:
            raise BadArgument()
        elif ctx.message.channel_mentions:
            if len(ctx.message.channel_mentions) > 1:
                raise BadArgument()
            else:
                m = ctx.message.channel_mentions[0].id
        elif ctx.message.mentions:
            if len(ctx.message.mentions) > 1:
                raise BadArgument()
            else:
                m = ctx.message.mentions[0]
                if not m.dm_channel:
                    await m.create_dm()
                m = m.dm_channel.id
        else:
            m = ctx.channel.id
        s = db.Session()
        c = query_calendar(name, ctx.guild.id)
        n = s.query(db.CalendarNotify).filter(db.CalendarNotify.channel == m) \
            .filter(db.CalendarNotify.calendar_id == c.id) \
            .first()
        if action is None and not n:
            s.add(db.CalendarNotify(m, c.id))
        elif action == "rm" and n:
            s.delete(n)
        else:
            s.close()
            raise BadArgument()
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @calendar_notify.group("list")
    @commands.guild_only()
    async def calendar_notify_list(self, ctx: commands.Context):
        s = db.Session()
        embed = Embed(title="Notify list")
        for c in s.query(db.Calendar).filter(db.Calendar.server == ctx.guild.id).all():
            notify = []
            for n in c.calendars_notify:
                ch = self.bot.get_channel(n.channel)
                if type(ch) == TextChannel:
                    notify.append(ch.mention)
                elif type(ch) == DMChannel:
                    notify.append(ch.recipient.mention)
            embed.add_field(name=c.name, value="\n".join(notify) or "Nothing here")
        await ctx.send(embed=embed)

    @calendar_notify.group("trigger", pass_context=True)
    @commands.guild_only()
    async def calendar_notify_trigger(self, ctx: commands.Context, name: str):
        c = query_calendar(name, ctx.guild.id)
        now = datetime.now()
        await c.notify(self.bot, c.events(now, now)[0])

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
