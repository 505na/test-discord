from discord.ext import commands


class ServerCog(commands.Cog):
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id

    async def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.guild is not None and ctx.guild.id == self.guild_id
