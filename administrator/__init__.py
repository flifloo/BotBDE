from administrator.config import config
import db
from discord.ext import commands

bot = commands.Bot(command_prefix=config.get("prefix"))

import extensions

bot.run(config.get("token"))