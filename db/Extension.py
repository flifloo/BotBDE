from db import Base
from sqlalchemy import Column, String, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import relationship


class Extension(Base):
    __tablename__ = "extension"
    name = Column(String, primary_key=True)
    default_state = Column(Boolean, nullable=False, default=True)
    extension_state = relationship("ExtensionState", backref="extension")

    def __init__(self, name: int, default_state: bool = True):
        self.name = name
        self.default_state = default_state


class ExtensionState(Base):
    __tablename__ = "extension_state"
    extension_name = Column(String, ForeignKey("extension.name"), primary_key=True)
    guild_id = Column(BigInteger, nullable=False, primary_key=True)
    state = Column(Boolean, nullable=False, default=True)

    def __init__(self, extension_name: str, guild_id: int, state: bool = True):
        self.extension_name = extension_name
        self.guild_id = guild_id
        self.state = state
