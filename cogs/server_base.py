from discord.ext import commands


class ServerCog(commands.Cog):
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id

    async def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.guild is not None and ctx.guild.id == self.guild_id

    def cog_unload(self):
        command_names = getattr(self.bot, "server_command_names", {})
        for guild_id, command_name in tuple(command_names):
            if guild_id == self.guild_id:
                del command_names[(guild_id, command_name)]


async def register_server_cog(bot: commands.Bot, cog: ServerCog):
    command_names = getattr(bot, "server_command_names", {})
    registered_names = {}

    for command in cog.get_commands():
        public_name = command.name
        registered_name = f"{public_name}__guild_{cog.guild_id}"
        command.name = registered_name
        command.aliases = []
        command.hidden = True
        registered_names[(cog.guild_id, public_name.lower())] = registered_name.lower()

    await bot.add_cog(cog)
    command_names.update(registered_names)
    bot.server_command_names = command_names
