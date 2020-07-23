from discord.ext import commands
from discord import Member, Embed
from discord.ext.commands import BadArgument

from administrator.logger import logger
from administrator import db, config


def check_greetings_message_type(message_type):
    if message_type not in ["join", "leave"]:
        raise BadArgument()


extension_name = "greetings"
logger = logger.getChild(extension_name)


class Greetings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group("greetings", pass_context=True)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def greetings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.greetings_help)

    @greetings.group("help", pass_context=True)
    async def greetings_help(self, ctx: commands.Context):
        embed = Embed(title="Greetings help")
        embed.add_field(name="set <join/leave> <message>", value="Set the greetings message\n"
                                                                 "`{}` will be replace by the username",
                        inline=False)
        embed.add_field(name="show <join/leave>", value="Show the greetings message", inline=False)
        embed.add_field(name="toggle <join/leave>", value="Enable or disable the greetings message", inline=False)
        await ctx.send(embed=embed)

    @greetings.group("set", pass_context=True)
    async def greetings_set(self, ctx: commands.Context, message_type: str):
        check_greetings_message_type(message_type)
        message = ctx.message.content.replace(config.get("prefix")+"greetings set " + message_type, "").strip()
        s = db.Session()
        m = s.query(db.Greetings).filter(db.Greetings.guild == ctx.guild.id).first()
        if not m:
            m = db.Greetings(ctx.guild.id)
            s.add(m)
        setattr(m, message_type+"_enable", True)
        setattr(m, message_type+"_message", message)
        s.commit()
        await ctx.message.add_reaction("\U0001f44d")

    @greetings.group("show", pass_context=True)
    async def greetings_show(self, ctx: commands.Context, message_type: str):
        check_greetings_message_type(message_type)
        s = db.Session()
        m = s.query(db.Greetings).filter(db.Greetings.guild == ctx.guild.id).first()
        s.close()
        if not m:
            await ctx.send(f"No {message_type} message set !")
        else:
            if message_type == "join":
                await ctx.send(embed=m.join_embed(ctx.guild.name, str(ctx.message.author)))
            else:
                await ctx.send(m.leave_msg(str(ctx.message.author)))

    @greetings.group("toggle", pass_context=True)
    async def greetings_toggle(self, ctx: commands.Context, message_type: str):
        check_greetings_message_type(message_type)
        s = db.Session()
        m = s.query(db.Greetings).filter(db.Greetings.guild == ctx.guild.id).first()
        if not m:
            await ctx.send(f"No {message_type} message set !")
        else:
            setattr(m, message_type+"_enable", not getattr(m, message_type+"_enable"))
            s.commit()
            await ctx.send(f"{message_type.title()} message is " +
                           ("enable" if getattr(m, message_type+"_enable") else "disable"))
        s.close()

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        s = db.Session()
        m = s.query(db.Greetings).filter(db.Greetings.guild == member.guild.id).first()
        s.close()
        if m and m.join_enable:
            await member.send(embed=m.join_embed(member.guild.name, str(member)))

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        s = db.Session()
        m = s.query(db.Greetings).filter(db.Greetings.guild == member.guild.id).first()
        s.close()
        if m and m.leave_enable:
            await member.guild.system_channel.send(m.leave_msg(str(member)))


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Greetings(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Greetings")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
