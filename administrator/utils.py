import re
from datetime import timedelta

from discord.ext.commands import BadArgument
from sqlalchemy.orm import Session

import db


def time_pars(s: str) -> timedelta:
    match = re.fullmatch(r"(?:([0-9]+)W)*(?:([0-9]+)D)*(?:([0-9]+)H)*(?:([0-9]+)M)*(?:([0-9]+)S)*",
                         s.upper().replace(" ", "").strip())
    if match:
        w, d, h, m, s = match.groups()
        if any([w, d, h, m, s]):
            w, d, h, m, s = [i if i else 0 for i in [w, d, h, m, s]]
            return timedelta(weeks=int(w), days=int(d), hours=int(h), minutes=int(m), seconds=int(s))
    raise BadArgument()


def seconds_to_time_string(seconds: float) -> str:
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"""{f"{days}d {hours}h {minutes}m {seconds}s"
    if days > 0 else f"{hours}h {minutes}m {seconds}s"
    if hours > 0 else f"{minutes}m {seconds}s"
    if minutes > 0 else f"{seconds}s"}"""


def event_is_enabled(cog: str, guild_id: int, s: Session = None) -> bool:
    close = False
    if not s:
        s = db.Session()
        close = True

    es = s.query(db.ExtensionState).get((cog, guild_id))

    if close or (es and not es.state):
        s.close()

    if es:
        return es.state
    return True
