# Komendy przypisane do serwera

Dodaj plik `guild_<NAZWA_SERWERA>.py` w tym folderze, np.
`guild_Home_Alabama.py`. Bot automatycznie załaduje pliki zaczynające się
od `guild_` przy starcie. Nazwa pliku może być nazwą serwera, ale musi być
prawidłową nazwą modułu Pythona.

Każdy moduł serwerowy powinien zawierać cog dziedziczący po
`cogs.server_base.ServerCog`. Bazowy cog dopuszcza wykonanie jego komend
wyłącznie na serwerze, którego ID podano w konstruktorze. Nazwa klasy cog-a
musi być unikalna w całym bocie, więc użyj innej nazwy dla każdego serwera.

Przykład zawartości pliku `guild_Home_Alabama.py`:

```python
import discord
from discord.ext import commands

from cogs.server_base import ServerCog

GUILD_ID = 1526655387804111068


class HomeAlabamaCommands(ServerCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot, GUILD_ID)

    @commands.command()
    async def tylko_tutaj(self, ctx: commands.Context):
        await ctx.send(f"Ta komenda działa na serwerze {self.guild_id}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(HomeAlabamaCommands(bot))
```

Użyj prawdziwego numerycznego ID serwera w `GUILD_ID`. Nazwa pliku jest tylko
czytelną etykietą; to ID w kodzie przypisuje komendy do właściwego serwera.
Nazwy komend muszą być unikalne w całym bocie, również między plikami
serwerowymi. Aktualne przykłady rejestrują `!home_alabama`, `!ksiądz`
i `!las_sosnowy`.
