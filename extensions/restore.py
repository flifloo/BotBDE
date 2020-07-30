from discord.ext import commands
from backup_bot.logger import logger
from os.path import isdir
from os import mkdir, remove
import shelve
from requests import get
from discord import Embed

extension_name = "restore"
logger = logger.getChild(extension_name)


@commands.command("restore")
async def restore_cmd(ctx: commands.Context):
    if len(ctx.message.attachments) != 1:
        await ctx.send("No backup file given ! \N{cross mark}")
    else:
        embed = Embed(title="Restore", description="In progress... \N{hourglass}")
        msg = await ctx.send(embed=embed)

        file = get(ctx.message.attachments[0].url, stream=True)
        file_name = f"backup/{ctx.message.author.id}"
        with open(file_name + ".db", "w+b") as f:
            for i in file.iter_content():
                f.write(i)
        with shelve.open(file_name) as file:
            categories = {}
            for c in file["categories"]:
                categories[c] = await ctx.guild.create_category(name=file["categories"][c]["name"],
                                                                reason=f"Backup restore by {ctx.message.author}")
            for c in file["channels"]:
                embed_field_name = file["channels"][c]["name"]
                category = None
                if file["channels"][c]["category_id"]:
                    category = categories[file["channels"][c]["category_id"]]
                    embed_field_name = f"{category.name} > {embed_field_name}"

                embed = msg.embeds[0]
                if len(embed.fields) != 0:
                    embed.set_field_at(-1, name=embed.fields[-1].name, value="\N{check mark}", inline=False)
                embed.add_field(name=embed_field_name, value="\N{hourglass}", inline=False)
                await msg.edit(embed=embed)

                chan = await ctx.guild.create_text_channel(name=file["channels"][c]["name"],
                                                           category=category,
                                                           topic=file["channels"][c]["topic"],
                                                           slowmode_delay=file["channels"][c]["slowmode_delay"],
                                                           nsfw=file["channels"][c]["nsfw"],
                                                           reason=f"Backup restore by {ctx.message.author}")
                hook = await chan.create_webhook(name="BackupBot",
                                                 avatar=None,
                                                 reason=f"Backup restore by {ctx.message.author}")
                for m in file["channels"][c]["messages"][::-1]:
                    user = file["users"][m["author_id"]]
                    edit = ""
                    if m["edited_at"]:
                        edit = f", edited at: {m['edited_at']}"
                    content = f"`created: {m['created_at']}{edit}`" + "\n" + m["content"]
                    avatar = None
                    if user["avatar"]:
                        avatar = f"https://cdn.discordapp.com/avatars/{m['author_id']}/{user['avatar']}.webp"
                    await hook.send(content=content,
                                    username=f"{user['display_name']} ({user['name']}#{user['discriminator']})",
                                    avatar_url=avatar,
                                    files=None,
                                    embeds=m["embeds"])
                await hook.delete()

        remove(file_name + ".db")
        embed = msg.embeds[0]
        embed.set_field_at(-1, name=embed.fields[-1].name, value="\N{check mark}", inline=False)
        embed.description = "Finish ! \N{check mark}"
        await msg.edit(embed=embed)


def setup(bot: commands.Bot):
    logger.info(f"Loading...")
    if not isdir("backup"):
        logger.info(f"Create backup folder")
        mkdir("backup")
    try:
        bot.add_command(restore_cmd)
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot: commands.Bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_command("restore")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
