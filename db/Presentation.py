from db import Base
from sqlalchemy import Column, Integer, BigInteger


class Presentation(Base):
    __tablename__ = "presentations"
    id = Column(Integer, primary_key=True)
    channel = Column(BigInteger, nullable=False)
    role = Column(BigInteger, nullable=False)
    guild = Column(BigInteger, nullable=False, unique=True)

    def __init__(self, guild: int, channel: int, role: int):
        self.guild = guild
        self.channel = channel
        self.role = role
