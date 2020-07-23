from discord import Embed

from db import Base
from sqlalchemy import Column, Integer, Text, Boolean, BigInteger


class Greetings(Base):
    __tablename__ = "greetings"
    id = Column(Integer, primary_key=True)
    join_message = Column(Text, nullable=False, default="")
    join_enable = Column(Boolean, nullable=False, default=False)
    leave_message = Column(Text, nullable=False, default="")
    leave_enable = Column(Boolean, nullable=False, default=False)
    guild = Column(BigInteger, nullable=False, unique=True)

    def __init__(self, guild: int):
        self.guild = guild

    def join_embed(self, guild_name: str,  user: str):
        embed = Embed()
        embed.add_field(name=f"Welcome to {guild_name} !", value=self.join_message.format(user))
        return embed

    def leave_msg(self, user: str):
        return self.leave_message.format(user)
