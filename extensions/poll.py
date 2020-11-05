from datetime import datetime

from discord.abc import GuildChannel
from discord.ext import commands
from discord import Embed, RawReactionActionEvent, RawMessageDeleteEvent, RawBulkMessageDeleteEvent, TextChannel, Guild
from discord.ext.commands import BadArgument

import db
from administrator.check import is_enabled
from administrator.logger import logger
from administrator.utils import event_is_enabled

extension_name = "poll"
logger = logger.getChild(extension_name)
REACTIONS = []
for i in range(10):
    REACTIONS.append(str(i)+"\ufe0f\u20E3")
REACTIONS.append("\U0001F51F")


class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "Create poll with a simple command"

    @commands.group("poll", pass_context=True)
    @is_enabled()
    @commands.guild_only()
    async def poll(self, ctx: commands.Context, name: str, *choices):
        if name == "help":
            await ctx.invoke(self.poll_help)
        else:
            multi = False
            if choices and choices[0] in ["multi", "m"]:
                multi = True
                choices = choices[1:]
            if len(choices) == 0 or len(choices) > 11:
                raise BadArgument()
            else:
                embed = Embed(title=f"Poll: {name}")
                embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
                embed.set_footer(text=f"Created: {ctx.message.created_at.strftime('%d/%m/%Y %H:%M')}")
                for i, choice in enumerate(choices):
                    embed.add_field(name=REACTIONS[i], value=choice, inline=False)
                message = await ctx.send(embed=embed)
                reactions = REACTIONS[0:len(choices)] + ["\U0001F5D1"]
                for reaction in reactions:
                    await message.add_reaction(reaction)
                s = db.Session()
                s.add(db.Polls(message.id, ctx.channel.id, ctx.guild.id, ctx.message.author.id, reactions, multi))
                s.commit()
                s.close()
                await ctx.message.delete()

    @poll.group("help", pass_context=True)
    async def poll_help(self, ctx: commands.Context):
        embed = Embed(title="Poll help")
        embed.add_field(name="poll <name> [multi|m] <Choice N°1> <Choice N°2> ... <Choice N°11>",
                        value="Create a poll, the argument multi (or m) after the name allow multiple response\n"
                              "User the \U0001F5D1 to close the poll",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if not payload.member:
            user = await self.bot.fetch_user(payload.user_id)
        else:
            user = payload.member

        if not user.bot:
            s = db.Session()
            if payload.guild_id and not event_is_enabled(self.qualified_name, payload.guild_id, s):
                return
            p = s.query(db.Polls).filter(db.Polls.message == payload.message_id).first()
            if p:
                message = await self.bot.get_channel(p.channel).fetch_message(p.message)
                if str(payload.emoji) not in eval(p.reactions):
                    await message.remove_reaction(payload.emoji, user)
                elif str(payload.emoji) == "\U0001F5D1":
                    if user.id != p.author:
                        await message.remove_reaction(payload.emoji, user)
                    else:
                        await self.close_poll(s, p)
                elif not p.multi:
                    f = False
                    for r in message.reactions:
                        if str(r.emoji) != str(payload.emoji):
                            async for u in r.users():
                                if u == user:
                                    await r.remove(user)
                                    f = True
                                    break
                            if f:
                                break
            s.close()

    async def close_poll(self, session: db.Session, poll: db.Polls):
        time = datetime.now()
        message = await self.bot.get_channel(poll.channel).fetch_message(poll.message)
        reactions = message.reactions
        await message.clear_reactions()
        embed = message.embeds[0]
        for i, f in enumerate(embed.fields):
            embed.set_field_at(i, name=f"{f.name} - {reactions[i].count-1}", value=f.value, inline=False)
        embed.set_footer(text=embed.footer.text + "\n" + f"Close: {time.strftime('%d/%m/%Y %H:%M')}")
        await message.edit(embed=embed)
        session.delete(poll)
        session.commit()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, message: RawMessageDeleteEvent):
        s = db.Session()
        p = s.query(db.Polls).filter(db.Polls.message == message.message_id).first()
        if p:
            s.delete(p)
            s.commit()
        s.close()

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, messages: RawBulkMessageDeleteEvent):
        s = db.Session()
        for p in s.query(db.Polls).filter(db.Polls.message.in_(messages.message_ids)).all():
            s.delete(p)
        s.commit()
        s.close()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: GuildChannel):
        if isinstance(channel, TextChannel):
            s = db.Session()
            for p in s.query(db.Polls).filter(db.Polls.channel == channel.id).all():
                s.delete(p)
            s.commit()
            s.close()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        s = db.Session()
        for p in s.query(db.Polls).filter(db.Polls.guild == guild.id).all():
            s.delete(p)
        s.commit()
        s.close()


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Poll(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Poll")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
