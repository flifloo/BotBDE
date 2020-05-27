from db import Base
from sqlalchemy import Column, Integer, String, BigInteger


class Calendar(Base):
    __tablename__ = "calendars"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    resources = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=False)
    server = Column(BigInteger, nullable=False)

    def __init__(self, name: str, resources: int, project_id: int, server: int):
        self.name = name
        self.resources = resources
        self.project_id = project_id
        self.server = server
