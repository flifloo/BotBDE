from db import Base
from sqlalchemy import Column, BigInteger, String


class PCP(Base):
    __tablename__ = "pcp"
    guild_id = Column(BigInteger, primary_key=True)
    roles_re = Column(String, nullable=False)
    start_role_re = Column(String)

    def __init__(self, guild_id: int, roles_re: str, start_role_re: str = None):
        self.guild_id = guild_id
        self.roles_re = roles_re
        if start_role_re:
            self.start_role_re = start_role_re
