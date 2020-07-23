from datetime import datetime

from discord.ext import commands
from discord import Member, Embed, Reaction

from administrator.logger import logger


extension_name = "poll"
logger = logger.getChild(extension_name)
REACTIONS = []
for i in range(10):
    REACTIONS.append(str(i)+"\ufe0f\u20E3")
REACTIONS.append("\U0001F51F")


class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.polls = {}

    @commands.group("poll", pass_context=True)
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
                await ctx.message.add_reaction("\u274C")
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
                message = await message.channel.fetch_message(message.id)
                self.polls[message.id] = {"multi": multi, "message": message, "author": ctx.message.author.id}
                await ctx.message.delete()

    @poll.group("help", pass_context=True)
    @commands.guild_only()
    async def poll_help(self, ctx: commands.Context):
        embed = Embed(title="poll help")
        embed.add_field(name="poll <name> [multi|m] <Choice N°1> <Choice N°2> ... <Choice N°11>",
                        value="Create a poll, the argument multi (or m) after the name allow multiple response\n"
                              "User the \U0001F5D1 to close the poll",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: Member):
        if not user.bot and reaction.message.id in self.polls:
            if reaction not in self.polls[reaction.message.id]["message"].reactions:
                await reaction.remove(user)
            elif str(reaction.emoji) == "\U0001F5D1":
                if user.id != self.polls[reaction.message.id]["author"]:
                    await reaction.remove(user)
                else:
                    await self.close_poll(reaction.message.id)
            elif not self.polls[reaction.message.id]["multi"]:
                f = False
                for r in reaction.message.reactions:
                    if str(r.emoji) != str(reaction.emoji):
                        async for u in r.users():
                            if u == user:
                                await r.remove(user)
                                f = True
                                break
                        if f:
                            break

    async def close_poll(self, id: int):
        time = datetime.now()
        message = await self.polls[id]["message"].channel.fetch_message(id)
        reactions = message.reactions
        await message.clear_reactions()
        embed = message.embeds[0]
        for i, f in enumerate(embed.fields):
            embed.set_field_at(i, name=f"{f.name} - {reactions[i].count-1}", value=f.value, inline=False)
        embed.set_footer(text=embed.footer.text + "\n" + f"Close: {time.strftime('%d/%m/%Y %H:%M')}")
        await message.edit(embed=embed)
        del self.polls[id]


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
