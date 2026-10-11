import random

from discord.ext import commands

from cogs.server_base import ServerCog, register_server_cog

GUILD_ID = 1034917608824246324


class LasSosnowyCommands(ServerCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot, GUILD_ID)

    @commands.command()
    async def las_sosnowy(self, ctx: commands.Context):
        await ctx.send(f"Ta komenda działa na serwerze {self.guild_id}.")

    def format_random_name(self, member):
        return f"`{member.display_name}`"

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
        await ctx.send(
            f"{self.format_random_name(first)} z miłą chęcią wyskoczy na kawkę z {self.format_random_name(second)}"
        )


async def setup(bot: commands.Bot):
    await register_server_cog(bot, LasSosnowyCommands(bot))
