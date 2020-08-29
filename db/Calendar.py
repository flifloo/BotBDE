import re
from datetime import datetime, timezone, timedelta

from discord import Embed
from discord.ext.commands import Bot
import ics
import requests
from sqlalchemy.orm import relationship, Session

from db import Base
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Text, DateTime

name_re = re.compile(r"([A-Z]+ [A-Z]+)")


def url(resources: int, project_id: int, first_date: datetime, last_date: datetime):
    first_date = first_date.strftime("%Y-%m-%d")
    last_date = last_date.strftime("%Y-%m-%d")
    return "http://adelb.univ-lyon1.fr/jsp/custom/modules/plannings/anonymous_cal.jsp?" \
           f"resources={resources}&projectId={project_id}&calType=ical&firstDate={first_date}&lastDate={last_date}"


class Calendar(Base):
    __tablename__ = "calendars"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    resources = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=False)
    server = Column(BigInteger, nullable=False)
    calendar = Column(Text)
    calendar_update = Column(DateTime)
    last_notify = Column(DateTime, nullable=False, default=datetime.now())

    calendars_notify = relationship("CalendarNotify", backref="calendar", lazy="subquery")

    def __init__(self, name: str, resources: int, project_id: int, server: int):
        self.name = name
        self.resources = resources
        self.project_id = project_id
        self.server = server

    def cal(self) -> ics.Calendar:
        now = datetime.now()
        if not self.calendar or self.calendar_update <= now - timedelta(minutes=30):
            first_date = now - timedelta(days=now.weekday())
            last_date = now + timedelta(days=31)
            self.calendar = requests.get(url(self.resources, self.project_id, first_date, last_date)).text
            self.calendar_update = now

        return ics.Calendar(self.calendar)

    def events(self, first_date: datetime.date, last_date: datetime.date) -> [ics.Event]:
        events = []
        for e in sorted(list(self.cal().events), key=lambda x: x.begin):
            e.begin = e.begin.astimezone(tz=None)
            e.end = e.end.astimezone(tz=None)
            e.organizer = name_re.findall(e.description)[0]
            if e.begin.date() >= first_date and e.end.date() <= last_date:
                events.append(e)
        return list(events)

    def week_embed(self, date: datetime.date):
        date -= timedelta(days=date.weekday())
        embed = Embed(title=f"Week calendar: {self.name}",
                      description=f"{date.strftime('%d/%m/%Y')} - {(date + timedelta(days=4)).strftime('%d/%m/%Y')}")

        for d in range(5):
            events = []
            for e in self.events(date, date):
                events.append(f"*{e.begin.strftime('%H:%M')} - {e.end.strftime('%H:%M')}*: "
                              f"**{e.name}** | {e.location} - {e.organizer}")
            embed.add_field(name=date.strftime("%d/%m/%Y"), value="\n".join(events) or "Nothing !", inline=False)
            date = date + timedelta(days=1)

        return embed


class CalendarNotify(Base):
    __tablename__ = "calendars_notify"
    channel = Column(BigInteger, primary_key=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id"), primary_key=True)

    def __init__(self, channel: int, calender: int):
        self.channel = channel
        self.calendar_id = calender

    async def notify(self, bot: Bot, event: ics.Event):
        embed = Embed(title="Event is coming !")
        embed.add_field(name=f"{event.begin.strftime('%H:%M')} - {event.end.strftime('%H:%M')}",
                        value=f"{event.name} | {event.location} - {event.organizer}")
        channel = bot.get_channel(self.channel)
        if channel:
            await channel.send(embed=embed)

    async def next_day_resume(self, bot: Bot):
        channel = bot.get_channel(self.channel)
        if channel:
            await channel.send(embed=self.calendar.week_embed((datetime.now() + timedelta(days=1)).date()))
