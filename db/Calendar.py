import re
from datetime import datetime, timezone

from discord import Embed
from discord.ext.commands import Bot
import ics
import requests
from sqlalchemy.orm import relationship, Session

from db import Base
from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey

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

    calendars_notify = relationship("CalendarNotify", backref="calendar", lazy="subquery")

    def __init__(self, name: str, resources: int, project_id: int, server: int):
        self.name = name
        self.resources = resources
        self.project_id = project_id
        self.server = server

    def cal(self, first_date: datetime, last_date: datetime) -> ics.Calendar:
        return ics.Calendar(requests.get(url(self.resources, self.project_id, first_date, last_date)).text)

    def events(self, first_date: datetime, last_date: datetime) -> [ics.Event]:
        events = []
        for e in sorted(list(self.cal(first_date, last_date).events), key=lambda x: x.begin):
            e.begin = e.begin.replace(tzinfo=timezone.utc).astimezone(tz=None)
            e.end = e.begin.replace(tzinfo=timezone.utc).astimezone(tz=None)
            e.organizer = name_re.findall(e.description)[0]
            events.append(e)
        return events

    async def notify(self, bot: Bot, event: ics.Event):
        for n in self.calendars_notify:
            bot.loop.create_task(n.notify(bot, event))


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
        await bot.get_channel(self.channel).send(embed=embed)
