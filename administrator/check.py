from discord.ext import commands

import db


class ExtensionDisabled(commands.CheckFailure):
    pass


def is_enabled():
    async def check(ctx: commands.Context):
        if ctx.command.cog:
            s = db.Session()
            es = s.query(db.ExtensionState).get((ctx.command.cog.qualified_name, ctx.guild.id))
            s.close()
            if es and not es.state:
                raise ExtensionDisabled()
        return True
    return commands.check(check)
