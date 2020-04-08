from discord.ext import commands
from discord import Member, VoiceState, Embed
from discord.ext.commands import CommandNotFound

from bot_bde.logger import logger


extension_name = "speak"
logger = logger.getChild(extension_name)


class Speak(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.strict = False
        self.voice_chan = None
        self.waiting = []
        self.lastSpeaker = None

    @commands.group("speak", pass_context=True)
    @commands.guild_only()
    async def speak(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            if ctx.author.voice is None or ctx.author.voice.channel is None:
                await ctx.send("Your not in a voice channel !")
            elif self.voice_chan is None:
                await ctx.send("Voice channel not set !")
            elif ctx.author.voice.channel.id != self.voice_chan:
                await ctx.send("Your not in the good voice channel !")
            elif ctx.author.id in self.waiting:
                await ctx.message.add_reaction("\u274C")
            else:
                self.waiting.append(ctx.author.id)
                await ctx.message.add_reaction("\U0001f44d")

    @speak.group("remove", pass_context=True)
    @commands.guild_only()
    async def speak_remove(self, ctx: commands.Context):
        if len(ctx.message.mentions) != 0:
            if self.voice_chan and ctx.guild.get_channel(self.voice_chan).permissions_for(ctx.author).mute_members:
                for speaker in ctx.message.mentions:
                    self.waiting.remove(speaker.id)
                await ctx.message.add_reaction("\U0001f44d")
            else:
                await ctx.message.add_reaction("\u274C")
        elif ctx.author.id in self.waiting:
            self.waiting.remove(ctx.author.id)
            await ctx.message.add_reaction("\U0001f44d")
        else:
            await ctx.message.add_reaction("\u274C")

    @speak.group("list", pass_context=True)
    @commands.guild_only()
    async def speak_list(self, ctx: commands.Context):
        if ctx.author.voice.channel is None or not self.voice_chan:
            await ctx.message.add_reaction("\u274C")
        else:
            embed = Embed(title="Waiting list")
            for i, speaker in enumerate(self.waiting):
                embed.add_field(name=f"N°{i+1}", value=ctx.guild.get_member(speaker).display_name, inline=True)
            await ctx.send(embed=embed)

    @speak.group("next", pass_context=True)
    @commands.guild_only()
    async def speak_next(self, ctx: commands.Context):
        if not self.voice_chan or not ctx.guild.get_channel(self.voice_chan).permissions_for(ctx.author).mute_members:
            await ctx.message.add_reaction("\u274C")
        else:
            if self.lastSpeaker:
                self.waiting.remove(self.lastSpeaker)
                if self.strict:
                    await ctx.guild.get_member(self.lastSpeaker).edit(mute=True)
            if len(self.waiting) != 0:
                user : Member = ctx.guild.get_member(self.waiting[0])
                self.lastSpeaker = self.waiting[0]
                await ctx.send(f"It's {user.mention} turn")
                if self.strict:
                    await user.edit(mute=False)
            else:
                self.lastSpeaker = None
                await ctx.send("Nobody left !")

    @speak.group("help", pass_context=True)
    @commands.guild_only()
    async def speak_help(self, ctx: commands.Context):
        embed = Embed(title="Speak help")
        embed.add_field(name="speak", value="Join the waiting list", inline=False)
        embed.add_field(name="speak remove [@pepole, @...]",
                        value="Remove yourself or mentioned person from the waiting list", inline=False)
        embed.add_field(name="speak list", value="Show the waiting list", inline=False)
        embed.add_field(name="Speak setup [strict]",
                        value="Set your current voice channel as the speak channel, you cant add the argument `strict` "
                              "to mute everyone except you and the current speaker", inline=False)
        embed.add_field(name="speak next",
                        value="Give the turn to the next waiter, if strict mode is enabled the last person get muted "
                              "and the next unmuted", inline=False)
        embed.add_field(name="speak mute", value="Mute everyone on the speak channel except you", inline=False)
        embed.add_field(name="speak unmute", value="Unmute everyone on the speak channel except you", inline=False)
        embed.add_field(name="speak clear", value="Clear the speak by unmute everyone and forget the list & channel",
                        inline=False)
        await ctx.send(embed=embed)

    @speak.group("setup", pass_context=True)
    @commands.guild_only()
    async def speak_setup(self, ctx: commands.Context, *args):
        if not ctx.author.voice.channel.permissions_for(ctx.author).mute_members:
            await ctx.message.add_reaction("\u274C")
        else:
            if len(args) != 0 and args[0] == "strict":
                self.strict = True
                for client in ctx.author.voice.channel.members:
                    if client != ctx.author and not client.bot:
                        await client.edit(mute=True)
            self.voice_chan = ctx.author.voice.channel.id
            await ctx.message.add_reaction("\U0001f44d")

    @speak.group("clear", pass_context=True)
    @commands.guild_only()
    async def speak_clear(self, ctx: commands.Context):
        speak_channel = ctx.guild.get_channel(self.voice_chan)
        if not self.voice_chan or not speak_channel.permissions_for(ctx.author).mute_members:
            await ctx.message.add_reaction("\u274C")
        else:
            self.waiting = []
            self.lastSpeaker = None
            for client in speak_channel.members:
                if client != ctx.author and not client.bot:
                    await client.edit(mute=False)
            self.strict = False
            self.voice_chan = None
            await ctx.message.add_reaction("\U0001f44d")

    @speak.group("mute", pass_context=True)
    @commands.guild_only()
    async def speak_mute(self, ctx: commands.Context):
        if ctx.author.voice is None or ctx.author.voice.channel is None or \
                not ctx.author.voice.channel.permissions_for(ctx.author).mute_members:
            await ctx.message.add_reaction("\u274C")
        else:
            for client in ctx.author.voice.channel.members:
                if client != ctx.author and not client.bot:
                    await client.edit(mute=True)
            await ctx.message.add_reaction("\U0001f44d")

    @speak.group("unmute", pass_context=True)
    @commands.guild_only()
    async def speak_unmute(self, ctx: commands.Context):
        if ctx.author.voice is None or ctx.author.voice.channel is None or \
                not ctx.author.voice.channel.permissions_for(ctx.author).mute_members:
            await ctx.message.add_reaction("\u274C")
        else:
            for client in ctx.author.voice.channel.members:
                if client != ctx.author and not client.bot:
                    await client.edit(mute=False)
            await ctx.message.add_reaction("\U0001f44d")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if (before is None or before.channel is None or before.channel.id != self.voice_chan) and\
                (after is not None and after.channel is not None and after.channel.id == self.voice_chan and self.strict):
            await member.edit(mute=True)
        elif (before is not None and before.channel is not None and before.channel.id == self.voice_chan) and\
                (after is not None and after.channel is not None and after.channel.id != self.voice_chan):
            await member.edit(mute=False)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, CommandNotFound):
            await ctx.message.add_reaction("\u2753")
        else:
            await ctx.send("An error occurred !")
            raise error


def setup(bot):
    logger.info(f"Loading...")
    try:
        bot.add_cog(Speak(bot))
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Speak")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
