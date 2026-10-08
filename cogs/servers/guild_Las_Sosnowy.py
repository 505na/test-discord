from discord.ext import commands

from cogs.server_base import ServerCog

GUILD_ID = 1034917608824246324


class ServerCommands(ServerCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot, GUILD_ID)

    @commands.command()
    async def las_sosnowy(self, ctx: commands.Context):
        await ctx.send(f"Ta komenda działa na serwerze {self.guild_id}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerCommands(bot))
