from bot_bde.logger import logger
from os.path import isfile
from json import load

logger = logger.getChild("Config")

if not isfile("config.json"):
    logger.critical("Config file not found !")
    exit(1)

config = {}
with open("config.json") as conf:
    logger.info("Loading configuration")
    try:
        config.update(load(conf))
    except Exception as e:
        logger.critical(f"Fail to load configuration: {e}")
        exit(1)
    else:
        logger.info("Configuration load successful")
