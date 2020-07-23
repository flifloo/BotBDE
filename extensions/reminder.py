import re
from datetime import datetime, timedelta

from discord.ext import commands
from discord import Embed
from discord.ext.commands import BadArgument
from discord.ext import tasks

from administrator.logger import logger
from administrator import db


extension_name = "reminders"
logger = logger.getChild(extension_name)


def time_pars(s: str) -> timedelta:
    match = re.fullmatch(r"(?:([0-9]+)W)*(?:([0-9]+)D)*(?:([0-9]+)H)*(?:([0-9]+)M)*(?:([0-9]+)S)*",
                         s.upper().replace(" ", "").strip())
    if match:
        w, d, h, m, s = match.groups()
        if any([w, d, h, m, s]):
            w, d, h, m, s = [i if i else 0 for i in [w, d, h, m, s]]
            return timedelta(weeks=int(w), days=int(d), hours=int(h), minutes=int(m), seconds=int(s))
    raise BadArgument()


class Reminders(commands.Cog, name="Reminder"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def description(self):
        return "Create and manage reminders"

    @commands.group("reminder", pass_context=True)
    async def reminder(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.reminder_help)

    @reminder.group("help", pass_context=True)
    async def reminder_help(self, ctx: commands.Context):
        embed = Embed(title="Reminder help")
        embed.add_field(name="reminder add <message> <time>", value="Add a reminder to your reminders list\n"
                                                                    "Time: ?D?H?M?S", inline=False)
        embed.add_field(name="reminder list", value="Show your tasks list", inline=False)
        embed.add_field(name="reminder remove [N°]", value="Show your tasks list with if no id given\n"
                                                           "Remove the task withe the matching id", inline=False)
        await ctx.send(embed=embed)

    @reminder.group("add", pass_context=True)
    async def reminder_add(self, ctx: commands.Context, message: str, time: str):
        time = time_pars(time)
        now = datetime.now()
        s = db.Session()
        s.add(db.Task(message, ctx.author.id, ctx.channel.id, now + time, ctx.message.created_at))
        s.commit()
        s.close()

        hours, seconds = divmod(time.seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        await ctx.send(f"""Remind you in {f"{time.days}d {hours}h {minutes}m {seconds}s"
        if time.days > 0 else f"{hours}h {minutes}m {seconds}s"
        if hours > 0 else f"{minutes}m {seconds}s"
        if minutes > 0 else f"{seconds}s"} !""")

    @reminder.group("list", pass_context=True)
    async def reminder_list(self, ctx: commands.Context):
        embed = Embed(title="Tasks list")
        s = db.Session()
        for t in s.query(db.Task).filter(db.Task.user == ctx.author.id).all():
            embed.add_field(name=f"N°{t.id} | {t.date.strftime('%d/%m/%Y %H:%M')}", value=f"{t.message}", inline=False)
        s.close()
        await ctx.send(embed=embed)

    @reminder.group("remove", pass_context=True)
    async def reminder_remove(self, ctx: commands.Context, n: int = None):
        if n is None:
            await ctx.invoke(self.reminder_list)
        else:
            s = db.Session()
            t = s.query(db.Task).filter(db.Task.id == n).first()
            if t and t.user == ctx.author.id:
                s.delete(t)
                s.commit()
                s.close()
                await ctx.message.add_reaction("\U0001f44d")
            else:
                s.close()
                raise BadArgument()

    @tasks.loop(minutes=1)
    async def reminders_loop(self):
        s = db.Session()
        for t in s.query(db.Task).filter(db.Task.date <= datetime.now()).all():
            self.bot.loop.create_task(self.reminder_exec(t))
            s.delete(t)

        s.commit()
        s.close()

    async def reminder_exec(self, task: db.Task):
        embed = Embed(title="You have a reminder !")
        user = self.bot.get_user(task.user)
        embed.set_author(name=f"{user.name}#{user.discriminator}", icon_url=user.avatar_url)
        embed.add_field(name=str(task.creation_date.strftime('%d/%m/%Y %H:%M')), value=task.message)
        await (await self.bot.get_channel(task.channel).send(f"{user.mention}", embed=embed)).edit(content="")

    def cog_unload(self):
        self.reminders_loop.stop()


def setup(bot):
    logger.info(f"Loading...")
    try:
        reminders = Reminders(bot)
        bot.add_cog(reminders)
        reminders.reminders_loop.start()
    except Exception as e:
        logger.error(f"Error loading: {e}")
    else:
        logger.info(f"Load successful")


def teardown(bot):
    logger.info(f"Unloading...")
    try:
        bot.remove_cog("Reminders")
    except Exception as e:
        logger.error(f"Error unloading: {e}")
    else:
        logger.info(f"Unload successful")
