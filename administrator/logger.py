import logging
from logging import handlers
from os import mkdir
from os.path import isdir

if not isdir("../logs"):
    mkdir("../logs")

log_format = "{%(levelname)s}[%(asctime)s]: %(name)s | %(message)s"

logging.basicConfig(
    format=log_format,
    level=logging.INFO
)
logger = logging.getLogger("Administrator")
handler = handlers.TimedRotatingFileHandler("../logs/current.log", when="d", interval=1)
handler.suffix = "%Y-%m-%d"
handler.style = log_format
handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(handler)
