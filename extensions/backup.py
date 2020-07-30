import shelve
from collections import OrderedDict
from datetime import datetime
from os import mkdir
from os.path import isdir

from discord import File, Embed
from discord.ext import commands

from administrator.logger import logger


extension_name = "backup"
logger = logger.getChild(extension_name)


class Backup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "Backup all message on the guild"

    @commands.group("backup", pass_context=True)
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def backup(self, ctx: commands.Context):
        embed = Embed(title="Backup", description="In progress... \N{hourglass}")
        msg = await ctx.send(embed=embed)
        file_name = f"backup/{datetime.now().strftime('%d-%m-%Y %H:%M')}"
        with shelve.open(file_name, writeback=True) as file:
            file["channels"] = OrderedDict()
            file["users"] = OrderedDict()
            file["categories"] = OrderedDict()
            for c in ctx.guild.text_channels:
                embed_field_name = c.name
                if c.category:
                    embed_field_name = f"{c.category} > {embed_field_name}"
                    if c.category_id not in file["categories"]:
                        file["categories"][c.category_id] = {"name": c.category.name,
                                                             "position": c.category.position,
                                                             "nsfw": c.category.is_nsfw()}
                embed = msg.embeds[0]
                if len(embed.fields) != 0:
                    embed.set_field_at(-1, name=embed.fields[-1].name, value="\N{check mark}", inline=False)
                embed.add_field(name=embed_field_name, value="\N{hourglass}", inline=False)
                await msg.edit(embed=embed)
                file["channels"][c.id] = {"name": c.name,
                                          "id": c.id,
                                          "category_id": c.category_id,
                                          "topic": c.topic,
                                          "position": c.position,
                                          "slowmode_delay": c.slowmode_delay,
                                          "nsfw": c.is_nsfw(),
                                          "messages": []}
                async for m in c.history(limit=None):
                    if m.author.id not in file["users"]:
                        file["users"][m.author.id] = {"name": m.author.name,
                                                      "discriminator": m.author.discriminator,
                                                      "display_name": m.author.display_name,
                                                      "avatar": m.author.avatar}
                    file["channels"][c.id]["messages"].append({"author_id": m.author.id,
                                                               "content": m.content,
                                                               "embeds": m.embeds,
                                                               # "attachments": m.attachments,
                                                               "pinned": m.pinned,
                                                               "reactions": m.reactions,
                                                               "created_at": m.created_at,
                                                               "edited_at": m.edited_at})
        embed = msg.embeds[0]
        embed.set_field_at(-1, name=embed.fields[-1].name, value="\N{check mark}", inline=False)
        embed.description = "Finish ! \N{check mark}"
        await msg.edit(embed=embed)
        await ctx.send(file=File(file_name + ".db", "backup.db"))


def setup(bot):
    logger.info(f"Loading...")
    if not isdir("backup"):
        logger.info(f"Create backup folder")
        mkdir("backup")
    try:
        bot.add_cog(Backup(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Backup")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
