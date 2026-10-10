import random

from discord.ext import commands

from cogs.server_base import ServerCog

GUILD_ID = 1526655387804111068


class HomeAlabamaCommands(ServerCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot, GUILD_ID)

    @commands.command()
    async def home_alabama(self, ctx: commands.Context):
        await ctx.send(f"Ta komenda działa na serwerze {self.guild_id}.")

    @commands.command()
    async def cwel(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if not members:
            await ctx.send("Nie ma żadnych osób do wylosowania.")
            return

        target = random.choice(members)
        await ctx.send(f"Największym cwelem jest nikt inny niż {target.mention}")

    @commands.command(name="ksiądz")
    async def ksiadz(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if not members:
            await ctx.send("Nie ma żadnych osób do wylosowania.")
            return

        target = random.choice(members)
        percent = random.randint(0, 100)
        await ctx.send(
            f"Jest {percent}% szans, że {target.mention} jest księdzem i kocha dzieci."
        )

    @commands.command()
    async def zdzira(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if len(members) < 2:
            await ctx.send("Potrzebuję co najmniej dwóch osób do wylosowania.")
            return

        first, second = random.sample(members, 2)
        await ctx.send(f"Zdzira {first.mention} zostaje {second.mention}")

    @commands.command()
    async def randka(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if len(members) < 2:
            await ctx.send("Potrzebuję co najmniej dwóch osób do wylosowania.")
            return

        first, second = random.sample(members, 2)
        await ctx.send(f"{first.mention} idzie na randkę z {second.mention}")

    @commands.command()
    async def kawa(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if len(members) < 2:
            await ctx.send("Potrzebuję co najmniej dwóch osób do wylosowania.")
            return

        first, second = random.sample(members, 2)
        await ctx.send(f"{first.mention} z miłą chęcią wyskoczy na kawkę z {second.mention}")


async def setup(bot: commands.Bot):
    await bot.add_cog(HomeAlabamaCommands(bot))
