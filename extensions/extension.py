from traceback import format_exc

from discord.ext import commands
from discord import Embed, Guild
from discord.ext.commands import MissingPermissions, BadArgument

import db
from administrator.logger import logger


extension_name = "extension"
logger = logger.getChild(extension_name)


class Extension(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "Manage bot's extensions"

    @commands.group("extension", pass_context=True)
    async def extension(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.extension_help)

    @extension.group("help", pass_context=True)
    async def extension_help(self, ctx: commands.Context):
        embed = Embed(title="Extension help")
        if await self.extension_list.can_run(ctx):
            embed.add_field(name="extension list", value="List all enabled extensions", inline=False)
        if await self.extension_enable.can_run(ctx):
            embed.add_field(name="extension enable", value="Enable an extensions", inline=False)
        if await self.extension_disable.can_run(ctx):
            embed.add_field(name="extension disable", value="Disable an extensions", inline=False)
        if await self.extension_load.can_run(ctx):
            embed.add_field(name="extension loaded", value="List all loaded extensions", inline=False)
        if await self.extension_load.can_run(ctx):
            embed.add_field(name="extension load <name>", value="Load an extension", inline=False)
        if await self.extension_unload.can_run(ctx):
            embed.add_field(name="extension unload <name>", value="Unload an extension", inline=False)
        if await self.extension_reload.can_run(ctx):
            embed.add_field(name="extension reload <name>", value="Reload an extension", inline=False)
        if not embed.fields:
            raise MissingPermissions(None)
        await ctx.send(embed=embed)

    @extension.group("list", pass_context=True)
    @commands.has_guild_permissions(administrator=True)
    async def extension_list(self, ctx: commands.Context):
        s = db.Session()
        embed = Embed(title="Extensions list")
        for es in s.query(db.ExtensionState).filter(db.ExtensionState.guild_id == ctx.guild.id):
            embed.add_field(name=es.extension_name, value="Enable" if es.state else "Disable")
        await ctx.send(embed=embed)

    @extension.group("enable", pass_context=True)
    @commands.has_guild_permissions(administrator=True)
    async def extension_enable(self, ctx: commands.Context, name: str):
        s = db.Session()
        es = s.query(db.ExtensionState).get((name, ctx.guild.id))
        if not es or es.state:
            raise BadArgument()
        es.state = True
        s.add(es)
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @extension.group("disable", pass_context=True)
    @commands.has_guild_permissions(administrator=True)
    async def extension_disable(self, ctx: commands.Context, name: str):
        s = db.Session()
        es = s.query(db.ExtensionState).get((name, ctx.guild.id))
        if not es or not es.state:
            raise BadArgument()
        es.state = False
        s.add(es)
        s.commit()
        s.close()
        await ctx.message.add_reaction("\U0001f44d")

    @extension.group("loaded", pass_context=True)
    @commands.is_owner()
    async def extension_loaded(self, ctx: commands.Context):
        embed = Embed(title="Extensions loaded")
        for extension in self.bot.extensions:
            embed.add_field(name=extension, value="Loaded", inline=False)
        await ctx.send(embed=embed)

    @extension.group("load", pass_context=True)
    @commands.is_owner()
    async def extension_load(self, ctx: commands.Context, name: str):
        try:
            self.bot.load_extension(name)
        except Exception as e:
            await ctx.message.add_reaction("\u26a0")
            await ctx.send(f"{e.__class__.__name__}: {e}\n```{format_exc()}```")
        else:
            await ctx.message.add_reaction("\U0001f44d")

    @extension.group("unload", pass_context=True)
    @commands.is_owner()
    async def extension_unload(self, ctx: commands.Context, name: str):
        try:
            self.bot.unload_extension(name)
        except Exception as e:
            await ctx.message.add_reaction("\u26a0")
            await ctx.send(f"{e.__class__.__name__}: {e}\n```{format_exc()}```")
        else:
            await ctx.message.add_reaction("\U0001f44d")

    @extension.group("reload", pass_context=True)
    @commands.is_owner()
    async def extension_reload(self, ctx: commands.Context, name: str):
        try:
            self.bot.unload_extension(name)
            self.bot.load_extension(name)
        except Exception as e:
            await ctx.message.add_reaction("\u26a0")
            await ctx.send(f"{e.__class__.__name__}: {e}\n```{format_exc()}```")
        else:
            await ctx.message.add_reaction("\U0001f44d")

    @commands.Cog.listener()
    async def on_ready(self):
        s = db.Session()
        for guild in self.bot.guilds:
            for extension in filter(lambda x: x not in ["Extension", "Help"], self.bot.cogs):
                e = s.query(db.Extension).get(extension)
                if not e:
                    s.add(db.Extension(extension))
                    s.commit()
                es = s.query(db.ExtensionState).get((extension, guild.id))
                if not es:
                    s.add(db.ExtensionState(extension, guild.id))
                    s.commit()
        s.close()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        s = db.Session()
        for extension in s.query(db.Extension).all():
            s.add(db.ExtensionState(extension.name, guild.id))
        s.commit()
        s.close()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        s = db.Session()
        for es in s.query(db.ExtensionState).filter(db.ExtensionState.guild_id == guild.id):
            s.delete(es)
        s.commit()
        s.close()


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Extension(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Extension")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
