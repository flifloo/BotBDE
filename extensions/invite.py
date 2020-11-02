import re

from discord import Embed, Member, Guild
from discord.errors import Forbidden
from discord.ext import commands
from discord.ext.commands import BadArgument

import db
from administrator.logger import logger

extension_name = "invite"
logger = logger.getChild(extension_name)
role_mention_re = re.compile(r"<@&[0-9]+>")
channel_mention_re = re.compile(r"<#[0-9]+>")


class Invite(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invites = {}
        self.bot.loop.create_task(self.update_invites())

    def description(self):
        return "Get role from a special invite link"

    @commands.group("invite", pass_context=True)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def invite(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.invite_help)

    @invite.group("help", pass_context=True)
    async def invite_help(self, ctx: commands.Context):
        embed = Embed(title="Invite help")
        embed.add_field(name="invite create <#channel> <@role>", value="Create a invite link to a role", inline=False)
        embed.add_field(name="invite delete <code>", value="Remove a invite", inline=False)
        await ctx.send(embed=embed)

    @invite.group("create", pass_context=True)
    async def invite_add(self, ctx: commands.Context, channel: str, role: str):
        if not channel_mention_re.fullmatch(channel) or len(ctx.message.channel_mentions) != 1 or\
                not role_mention_re.fullmatch(role) or len(ctx.message.role_mentions) != 1:
            raise BadArgument()

        inv = await ctx.message.channel_mentions[0].create_invite()
        s = db.Session()
        s.add(db.InviteRole(ctx.guild.id, inv.code, ctx.message.role_mentions[0].id))
        s.commit()
        s.close()
        await ctx.send(f"Invite created: `{inv.url}`")

    @invite.group("delete", pass_context=True)
    async def invite_delete(self, ctx: commands.Context, code: str):
        inv = next(filter(lambda i: i.code == code, await ctx.guild.invites()), None)
        if not inv:
            raise BadArgument()

        s = db.Session()
        invite_role = s.query(db.InviteRole).get({"guild_id": ctx.guild.id, "invite_code": code})
        if not invite_role:
            s.close()
            raise BadArgument()
        s.delete(invite_role)
        s.commit()
        s.close()
        await inv.delete()
        await ctx.message.add_reaction("\U0001f44d")

    async def update_invites(self):
        for g in self.bot.guilds:
            self.invites[g.id] = await g.invites()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.update_invites()

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        user_invites = await member.guild.invites()
        for i in self.invites[member.guild.id]:
            for ui in user_invites:
                if i.code == ui.code and i.uses < ui.uses:
                    s = db.Session()
                    invite_role = s.query(db.InviteRole).get({"guild_id": member.guild.id, "invite_code": i.code})
                    s.close()
                    if invite_role:
                        try:
                            await member.add_roles(member.guild.get_role(invite_role.role_id))
                        except Forbidden:
                            pass
        self.invites[member.guild.id] = user_invites

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        s = db.Session()
        invite_role = s.query(db.InviteRole).get({"guild_id": invite.guild.id, "invite_code": invite.code})
        if invite_role:
            s.delete(invite_role)
            s.commit()
        s.close()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        self.invites[guild.id] = await guild.invites()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        s = db.Session()
        for g in s.query(db.InviteRole).filter(db.InviteRole.guild_id == guild.id).all():
            s.delete(g)
        s.commit()
        s.close()
        del self.invites[guild.id]


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Invite(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Invite")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
