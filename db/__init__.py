from administrator.config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
db = config.get("db")
args = {"pool_pre_ping": True, "pool_recycle": 3600}
if not db.startswith("sqlite:"):
    args.update({"pool_size": 0, "max_overflow": -1})
engine = create_engine(db, **args)
Session = sessionmaker(bind=engine)
Base = declarative_base()
from db.Task import Task
from db.Greetings import Greetings
from db.Presentation import Presentation
from db.RoRec import RoRec
from db.Polls import Polls
from db.Warn import Warn
from db.WarnAction import WarnAction
from db.InviteRole import InviteRole
from db.Tomuss import Tomuss
from db.PCP import PCP
from db.Extension import Extension, ExtensionState
Base.metadata.create_all(engine)
