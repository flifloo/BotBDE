from db import Base
from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from datetime import datetime


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    message = Column(String, nullable=False)
    user = Column(BigInteger, nullable=False)
    channel = Column(BigInteger, nullable=False)
    date = Column(DateTime, nullable=False)
    creation_date = Column(DateTime, nullable=False, default=datetime.now())

    def __init__(self, message: str, user: int, channel: int, date: datetime, creation_date: datetime = None):
        self.message = message
        self.user = user
        self.channel = channel
        self.date = date
        if creation_date:
            self.creation_date = creation_date
