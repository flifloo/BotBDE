from datetime import datetime

from db import Base
from sqlalchemy import Column, BigInteger, String, DateTime


class Tomuss(Base):
    __tablename__ = "tomuss"
    user_id = Column(BigInteger, primary_key=True)
    url = Column(String, nullable=False)
    last = Column(DateTime, nullable=False)

    def __init__(self, user_id: int, url: str, last: datetime):
        self.user_id = user_id
        self.url = url
        self.last = last
