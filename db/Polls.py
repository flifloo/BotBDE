from db import Base
from sqlalchemy import Column, Integer, BigInteger, String, Boolean


class Polls(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True)
    message = Column(BigInteger, nullable=False, unique=True)
    channel = Column(BigInteger, nullable=False)
    author = Column(BigInteger, nullable=False)
    reactions = Column(String, nullable=False)
    multi = Column(Boolean, nullable=False, default=False)

    def __init__(self, message: int, channel: int, author: int, reactions: [str], multi: bool = False):
        self.message = message
        self.channel = channel
        self.author = author
        self.reactions = str(reactions)
        self.multi = multi
