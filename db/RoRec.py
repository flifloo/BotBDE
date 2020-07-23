from db import Base
from sqlalchemy import Column, Integer, BigInteger, Boolean, Text


class RoRec(Base):
    __tablename__ = "rorec"
    id = Column(Integer, primary_key=True)
    message = Column(BigInteger, nullable=False, unique=True)
    channel = Column(BigInteger, name=False)
    guild = Column(BigInteger, nullable=False)
    one = Column(Boolean, nullable=False, default=False)
    data = Column(Text, nullable=False, default="{}")

    def __init__(self, message: int, channel: int, guild: int, one: bool = False):
        self.message = message
        self.channel = channel
        self.guild = guild
        self.one = one

    def get_data(self) -> dict:
        return eval(self.data)

    def set_data(self, data: dict):
        self.data = str(data)
