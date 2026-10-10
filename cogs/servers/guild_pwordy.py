import random

from discord.ext import commands

from cogs.server_base import ServerCog, register_server_cog

GUILD_ID = 1506035412978761738


class PwordyCommands(ServerCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot, GUILD_ID)

    def format_random_name(self, member):
        return f"`{member.display_name}`"

    @commands.command()
    async def pedały(self, ctx: commands.Context):
        await ctx.send(f"Ta komenda działa na serwerze {ctx.guild.id}.")

    @commands.command()
    async def cwel(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if not members:
            await ctx.send("Nie ma żadnych osób do wylosowania.")
            return

        target = random.choice(members)
        await ctx.send(f"Największym cwelem jest nikt inny niż {self.format_random_name(target)}")

    @commands.command(name="ksiądz")
    async def ksiadz(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if not members:
            await ctx.send("Nie ma żadnych osób do wylosowania.")
            return

        target = random.choice(members)
        percent = random.randint(0, 100)
        await ctx.send(
            f"Jest {percent}% szans, że {self.format_random_name(target)} jest księdzem i kocha dzieci."
        )

    @commands.command()
    async def zdzira(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if len(members) < 2:
            await ctx.send("Potrzebuję co najmniej dwóch osób do wylosowania.")
            return

        first, second = random.sample(members, 2)
        await ctx.send(f"Zdzirą {self.format_random_name(first)} zostaje {self.format_random_name(second)}")

    @commands.command()
    async def randka(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if len(members) < 2:
            await ctx.send("Potrzebuję co najmniej dwóch osób do wylosowania.")
            return

        first, second = random.sample(members, 2)
        await ctx.send(f"{self.format_random_name(first)} idzie na randkę z {self.format_random_name(second)}")

    @commands.command()
    async def kawa(self, ctx: commands.Context):
        members = [member for member in ctx.guild.members if not member.bot]
        if len(members) < 2:
            await ctx.send("Potrzebuję co najmniej dwóch osób do wylosowania.")
            return

        first, second = random.sample(members, 2)
        await ctx.send(f"{self.format_random_name(first)} z miłą chęcią wyskoczy na kawkę z {self.format_random_name(second)}")


async def setup(bot: commands.Bot):
    await register_server_cog(bot, PwordyCommands(bot))
