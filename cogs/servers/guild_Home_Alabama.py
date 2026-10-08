from discord.ext import commands

from cogs.server_base import ServerCog

GUILD_ID = 1526655387804111068


class HomeAlabamaCommands(ServerCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot, GUILD_ID)

    @commands.command()
    async def home_alabama(self, ctx: commands.Context):
        await ctx.send(f"Ta komenda działa na serwerze {self.guild_id}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(HomeAlabamaCommands(bot))
