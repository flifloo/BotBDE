from discord.ext import commands
from discord import Embed, Message
from discord.ext.commands import BadArgument

from administrator.logger import logger
from administrator import db


extension_name = "presentation"
logger = logger.getChild(extension_name)


class Presentation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "Give role to user who make a presentation in a dedicated channel"

    @commands.group("presentation", pass_context=True)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def presentation(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.presentation_help)

    @presentation.group("help", pass_context=True)
    async def presentation_help(self, ctx: commands.Context):
        embed = Embed(title="Presentation help", description="Give a role to a new member after a presentation")
        embed.add_field(name="set <#channel> <@role>", value="Set the presentation channel and the role to give",
                        inline=False)
        embed.add_field(name="disable", value="Disable the auto role give", inline=False)
        await ctx.send(embed=embed)

    @presentation.group("set", pass_context=True)
    async def presentation_set(self, ctx: commands.Context):
        if len(ctx.message.channel_mentions) != 1 and not len(ctx.message.role_mentions) != 1:
            raise BadArgument()
        s = db.Session()
        p = s.query(db.Presentation).filter(db.Presentation.guild == ctx.guild.id).first()
        if not p:
            p = db.Presentation(ctx.guild.id, ctx.message.channel_mentions[0].id, ctx.message.role_mentions[0].id)
            s.add(p)
        else:
            p.channel = ctx.message.channel_mentions[0].id
            p.role = ctx.message.role_mentions[0].id
        s.commit()
        await ctx.message.add_reaction("\U0001f44d")

    @presentation.group("disable", pass_context=True)
    async def presentation_disable(self, ctx: commands.Context):
        s = db.Session()
        p = s.query(db.Presentation).filter(db.Presentation.guild == ctx.guild.id).first()
        if not p:
            await ctx.send(f"Nothing to disable !")
        else:
            s.delete(p)
            s.commit()
            await ctx.message.add_reaction("\U0001f44d")
        s.close()

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.guild is not None:
            s = db.Session()
            p = s.query(db.Presentation).filter(db.Presentation.guild == message.guild.id).first()
            s.close()
            if p and p.channel == message.channel.id and p.role not in map(lambda x: x.id, message.author.roles):
                await message.author.add_roles(message.guild.get_role(p.role), reason="Presentation done")


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Presentation(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Presentation")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
