from discord.ext import commands
from backup_bot.logger import logger
from os.path import isdir
from os import mkdir
import shelve
from datetime import datetime
from discord import File, Embed
from collections import OrderedDict

extension_name = "backup"
logger = logger.getChild(extension_name)


@commands.command("backup")
async def backup_cmd(ctx: commands.Context):
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


def setup(bot: commands.Bot):
    logger.info(f"Loading...")
    if not isdir("backup"):
        logger.info(f"Create backup folder")
        mkdir("backup")
    try:
        bot.add_command(backup_cmd)
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot: commands.Bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_command("backup")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
