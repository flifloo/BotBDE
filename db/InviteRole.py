from db import Base
from sqlalchemy import Column, BigInteger, String


class InviteRole(Base):
    __tablename__ = "invite_role"
    guild_id = Column(BigInteger, primary_key=True)
    invite_code = Column(String, primary_key=True)
    role_id = Column(BigInteger, nullable=False)

    def __init__(self, guild_id: int, invite_code: str, role_id: int):
        self.guild_id = guild_id
        self.role_id = role_id
        self.invite_code = invite_code
