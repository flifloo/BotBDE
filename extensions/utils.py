from datetime import datetime

from discord import Embed, Member, Guild
from discord.ext import commands
from discord.ext.commands import BadArgument

from administrator.check import is_enabled
from administrator.logger import logger


extension_name = "utils"
logger = logger.getChild(extension_name)


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "Some tools"

    @commands.group("utils", pass_context=True)
    @is_enabled()
    async def utils(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.utils_help)

    @utils.group("help", pass_context=True)
    async def utils_help(self, ctx: commands.Context):
        embed = Embed(title="Utils help")
        if self.eval.can_run(ctx):
            embed.add_field(name="eval \`\`\`code\`\`\`", value="Execute some code", inline=False)
        embed.add_field(name="ping", value="Return the ping with the discord API", inline=False)
        await ctx.send(embed=embed)

    @commands.group("eval", pass_context=True)
    @commands.is_owner()
    async def eval(self, ctx: commands.Context):
        start = ctx.message.content.find("```")
        end = ctx.message.content.find("```", start+3)
        command = ctx.message.content[start+3:end]
        try:
            exec("async def __ex(self, ctx):\n" + command.replace("\n", "\n    "))
            out = str(await locals()["__ex"](self, ctx))
            if len(out) > 1994:
                while out:
                    await ctx.send(f"```{out[:1994]}```")
                    out = out[1994:]
            else:
                await ctx.send(f"```{out}```")
        except Exception as e:
            await ctx.send(f"```{e.__class__.__name__}: {e}```")

    @commands.group("ping", pass_context=True)
    @is_enabled()
    async def ping(self, ctx: commands.Context):
        start = datetime.now()
        msg = await ctx.send(f"Discord WebSocket latency: `{round(self.bot.latency*1000)}ms`")
        await msg.edit(content=msg.content+"\n"+f"Bot latency: `{round((msg.created_at - start).microseconds/1000)}ms`")

    @commands.group("info", pass_context=True)
    @is_enabled()
    async def info(self, ctx: commands.Context):
        if len(ctx.message.mentions) > 1:
            raise BadArgument()
        elif ctx.message.mentions:
            user: Member = ctx.message.mentions[0]
            embed = Embed(title=str(user))
            embed.set_author(name="User infos", icon_url=user.avatar_url)
            embed.add_field(name="Display name", value=user.display_name)
            embed.add_field(name="Joined at", value=user.joined_at)
            if user.premium_since:
                embed.add_field(name="Guild premium since", value=user.premium_since)
            embed.add_field(name="Top role", value=user.top_role)
            embed.add_field(name="Created at", value=user.created_at)
            embed.add_field(name="ID", value=user.id)
        else:
            guild: Guild = ctx.guild
            embed = Embed(title=str(guild))
            embed.set_author(name="Guild infos", icon_url=guild.icon_url)
            embed.add_field(name="Emojis", value=f"{str(len(guild.emojis))}/{guild.emoji_limit}")
            embed.add_field(name="Region", value=guild.region)
            embed.add_field(name="Owner", value=str(guild.owner))
            if guild.max_presences:
                embed.add_field(name="Max presences", value=guild.max_presences)
            if guild.max_video_channel_users:
                embed.add_field(name="Max video channel users", value=guild.max_video_channel_users)
            if guild.description:
                embed.add_field(name="Description", value=guild.description)
            embed.add_field(name="Two factor authorisation level", value=guild.mfa_level)
            embed.add_field(name="Verification level", value=guild.verification_level)
            embed.add_field(name="Explicit content filter", value=guild.explicit_content_filter)
            embed.add_field(name="Default notifications", value=guild.default_notifications)
            if guild.features:
                embed.add_field(name="Features", value=guild.features)
            if guild.splash:
                embed.add_field(name="Splash", value=guild.splash)
            embed.add_field(name="Premium",
                            value=f"Tier: {guild.premium_tier} | Boosts {guild.premium_subscription_count}")
            if guild.preferred_locale:
                embed.add_field(name="Preferred locale", value=guild.preferred_locale)
            if guild.discovery_splash:
                embed.add_field(name="Discovery splash", value=guild.discovery_splash)
            embed.add_field(name="Large", value=guild.large)
            embed.add_field(name="Members",
                            value=f"{len(guild.members)}{'/'+str(guild.max_members) if guild.max_members else ''} "
                                  f"| Bans: {len(await guild.bans())} | subscribers: {len(guild.premium_subscribers)}")
            embed.add_field(name="Channels",
                            value=f"Voice: {str(len(guild.voice_channels))} | Text: {str(len(guild.text_channels))} "
                                  "\n" + f"Total: {str(len(guild.channels))} | Categories: {str(len(guild.categories))}"
                            )
            embed.add_field(name="Roles", value=str(len(guild.roles)))
            embed.add_field(name="Invites", value=str(len(await guild.invites())))
            embed.add_field(name="Addons",
                            value=f"Webhooks: {len(await guild.webhooks())} | Integrations: {len(await guild.integrations())}")

            embed.add_field(name="System channel", value=str(guild.system_channel))
            if guild.rules_channel:
                embed.add_field(name="Rules channel", value=str(guild.rules_channel))
            if guild.public_updates_channel:
                embed.add_field(name="Public updates channel", value=str(guild.public_updates_channel))
            embed.add_field(name="Bitrate limit", value=guild.bitrate_limit)
            embed.add_field(name="Filesize limit", value=guild.filesize_limit)
            embed.add_field(name="Chunked", value=guild.chunked)
            embed.add_field(name="Shard ID", value=guild.shard_id)
            embed.add_field(name="Created at", value=guild.created_at)

        await ctx.send(embed=embed)


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Utils(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Utils")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
