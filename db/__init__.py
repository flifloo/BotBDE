from bot_bde.config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
engine = create_engine(config.get("db"))
Session = sessionmaker(bind=engine)
Base = declarative_base()
from db.Task import Task
from db.Calendar import Calendar, CalendarNotify
Base.metadata.create_all(engine)
