from datetime import timedelta

from db import Base
from sqlalchemy import Column, Integer, BigInteger, Float, String


class WarnAction(Base):
    __tablename__ = "warn_actions"
    id = Column(Integer, primary_key=True)
    guild = Column(BigInteger, nullable=False)
    count = Column(Float, nullable=False, unique=True)
    action = Column(String, nullable=False)
    duration = Column(BigInteger)

    def __init__(self, guild: int, count: int, action: str, duration: float = None):
        self.guild = guild
        self.count = count
        self.action = action
        self.duration = duration
