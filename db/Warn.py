from datetime import datetime

from discord import Embed

from db import Base
from sqlalchemy import Column, Integer, BigInteger, Text, DateTime


class Warn(Base):
    __tablename__ = "warns"
    id = Column(Integer, primary_key=True)
    user = Column(BigInteger, nullable=False)
    author = Column(BigInteger, nullable=False)
    guild = Column(BigInteger, nullable=False)
    description = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.now())

    def __init__(self, user: int, author: int, guild: int, description: str):
        self.user = user
        self.author = author
        self.guild = guild
        self.description = description
