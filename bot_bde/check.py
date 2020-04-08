from discord.ext import commands
from bot_bde import config


class NotOwner(commands.CheckFailure):
    pass


async def is_owner(ctx: commands.Context):
    return ctx.author.id == config.get("admin_id")
