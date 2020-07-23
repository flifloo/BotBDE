import re

from discord.abc import GuildChannel
from discord.ext import commands
from discord import Embed, RawReactionActionEvent, RawBulkMessageDeleteEvent, RawMessageDeleteEvent, NotFound, \
    InvalidArgument, HTTPException, TextChannel, Forbidden
from discord.ext.commands import BadArgument

from administrator import db
from administrator.logger import logger


extension_name = "rorec"
logger = logger.getChild(extension_name)

channel_id_re = re.compile(r"^<#([0-9]+)>$")


class RoRec(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.edits = {}

    def description(self):
        return "Create role-reaction message to give role from a reaction add"

    @staticmethod
    def get_message(session: db.Session, message_id: int, guild_id: int) -> db.RoRec:
        m = session.query(db.RoRec).filter(db.RoRec.message == message_id and db.RoRec.guild == guild_id).first()
        if not m:
            raise BadArgument()
        else:
            return m

    async def try_emoji(self, ctx: commands.Context, emoji: str):
        try:
            await ctx.message.add_reaction(emoji)
        except (HTTPException, NotFound, InvalidArgument):
            raise BadArgument()
        else:
            await (await ctx.channel.fetch_message(ctx.message.id)).remove_reaction(emoji, self.bot.user)

    @commands.group("rorec", pass_context=True)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def rorec(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.rorec_help)

    @rorec.group("help", pass_context=True)
    async def rorec_help(self, ctx: commands.Context):
        embed = Embed(title="Role-Reaction help")
        embed.add_field(name="new <title> <#channel> [description] [Only one (True/False)]",
                        value="Create a new role-reaction message on the mentioned channel.\n"
                              "You can specify a description and if you can pick only one role",
                        inline=False)
        embed.add_field(name="edit <message id>", value="Edit a role-reaction message\n"
                                                        "You can also add a ... reaction on the message to edit",
                        inline=False)
        embed.add_field(name="set <message_id> <emoji> <@role1> [@role2] ...",
                        value="Add/edit a emoji with linked roles", inline=False)
        embed.add_field(name="remove <message_id> <emoji>", value="Remove a emoji of a role-reaction message",
                        inline=False)
        embed.add_field(name="reload <message_id>", value="Reload the message and the reactions", inline=False)
        embed.add_field(name="delete <message_id>", value="Remove a role-reaction message", inline=False)
        await ctx.send(embed=embed)

    @rorec.group("new", pass_context=True)
    async def rorec_new(self, ctx: commands.Context, title: str, channel: str, description: str = "",
                        one: bool = False):
        channel = channel_id_re.findall(channel)
        if len(channel) != 1:
            raise BadArgument()
        channel = ctx.guild.get_channel(int(channel[0]))
        if not channel:
            raise BadArgument()

        if description in ["True", "False"]:
            one = True if description == "True" else False
            description = ""

        embed = Embed(title=title, description=description)
        embed.add_field(name="Roles", value="No role yet...")
        message = await channel.send(embed=embed)
        r = db.RoRec(message.id, channel.id, ctx.guild.id, one)
        s = db.Session()
        s.add(r)
        s.commit()
        await ctx.message.add_reaction("\U0001f44d")

    @rorec.group("edit", pass_context=True)
    async def rorec_edit(self, ctx: commands.Context, message_id: int):
        s = db.Session()
        m = s.query(db.RoRec).filter(db.RoRec.message == message_id and db.RoRec.guild == ctx.guild.id).first()
        s.close()
        if not m or message_id in self.edits:
            raise BadArgument()

        self.edits[message_id] = ctx
        embed = Embed(title="Edit role-reaction message")
        embed.add_field(name="", value="... Set emoji\n"
                                       "... Remove emoji\n"
                                       "... Switch only one role rule\n"
                                       "... Delete message\n"
                                       "... Exit")
        message = await ctx.send(embed=embed)
        for i in []:
            await message.add_reaction(i)

    @rorec.group("set", pass_context=True)
    async def rorec_set(self, ctx: commands.Context, message_id: int, emoji: str):
        s = db.Session()
        m = self.get_message(s, message_id, ctx.guild.id)

        if len(ctx.message.role_mentions) == 0:
            raise BadArgument()

        await self.try_emoji(ctx, emoji)

        data = m.get_data()
        data[emoji] = list(map(lambda x: x.id, ctx.message.role_mentions))
        m.set_data(data)
        await self.rorec_update(m)
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @rorec.group("remove", pass_context=True)
    async def rorec_remove(self, ctx: commands.Context, message_id: int, emoji: str):
        s = db.Session()
        m = self.get_message(s, message_id, ctx.guild.id)
        await self.try_emoji(ctx, emoji)

        data = m.get_data()
        if emoji not in data:
            raise BadArgument()
        del data[emoji]
        m.set_data(data)

        await self.rorec_update(m)
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @rorec.group("reload", pass_context=True)
    async def rorec_reload(self, ctx: commands.Context, message_id: int):
        s = db.Session()
        m = self.get_message(s, message_id, ctx.guild.id)

        await self.rorec_update(m)
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @rorec.group("delete", pass_context=True)
    async def rorec_delete(self, ctx: commands.Context, message_id: int):
        s = db.Session()
        m = self.get_message(s, message_id, ctx.guild.id)
        s.close()
        await (await self.bot.get_channel(m.channel).fetch_message(m.message)).delete()
        await ctx.message.add_reaction("\U0001f44d")

    async def rorec_update(self, m: db.RoRec):
        channel = self.bot.get_channel(m.channel)
        if not channel:
            pass
        message = await channel.fetch_message(m.message)
        if not message:
            pass
        embed: Embed = message.embeds[0]
        name = embed.fields[0].name
        embed.remove_field(0)
        value = ""
        data = m.get_data()
        await message.clear_reactions()
        for d in data:
            value += f"{d}: "
            value += ", ".join(map(lambda x: self.bot.get_guild(m.guild).get_role(x).mention, data[d]))
            value += "\n"
            await message.add_reaction(d)
        embed.add_field(name=name, value=value)
        await message.edit(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, message: RawMessageDeleteEvent):
        s = db.Session()
        r = s.query(db.RoRec).filter(db.RoRec.message == message.message_id).first()
        if r:
            s.delete(r)
            s.commit()
        s.close()

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, messages: RawBulkMessageDeleteEvent):
        s = db.Session()
        for id in messages.message_ids:
            r = s.query(db.RoRec).filter(db.RoRec.message == id).first()
            if r:
                s.delete(r)
        s.commit()
        s.close()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: GuildChannel):
        if isinstance(channel, TextChannel):
            s = db.Session()
            for r in s.query(db.RoRec).filter(db.RoRec.channel == channel.id).all():
                s.delete(r)
            s.commit()
            s.close()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        s = db.Session()
        m = s.query(db.RoRec).filter(db.RoRec.message == payload.message_id).first()
        s.close()
        if m and payload.member.id != self.bot.user.id:
            data = m.get_data()
            emoji = str(payload.emoji)
            if emoji in data:
                guild = self.bot.get_guild(payload.guild_id)
                roles = [guild.get_role(r) for r in data[emoji]]
                add = False

                if m.one:
                    del data[emoji]
                    remove_roles = []
                    [remove_roles.extend(map(lambda x: guild.get_role(x), data[e])) for e in data]
                    await payload.member.remove_roles(*remove_roles, reason="Only one role-reaction message")

                for r in filter(lambda x: x not in payload.member.roles, roles):
                    try:
                        await payload.member.add_roles(r, reason="Role-reaction message")
                        add = True
                    except Forbidden:
                        await payload.member.send("I don't have the permission to add a role to you !")

                if not add:
                    try:
                        await payload.member.remove_roles(*roles, reason="Role-reaction message")
                    except Forbidden:
                        await payload.member.send("I don't have the permission to remove one of your roles !")

            await (await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id))\
                .remove_reaction(payload.emoji, payload.member)


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(RoRec(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("RoRec")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
