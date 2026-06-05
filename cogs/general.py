import random
import discord
from discord.ext import commands


class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_random_name(self, member: discord.Member):
        return f"`{member.display_name}`"

    def random_member(self, guild, exclude=None):
        users = [
            m for m in guild.members
            if not m.bot and m != exclude
        ]

        if not users:
            return None

        return random.choice(users)

    @commands.command()
    async def test(self, ctx):
        await ctx.send("✅ Bot działa!")

    @commands.command()
    async def hug(self, ctx):
        target = self.random_member(ctx.guild, ctx.author)

        if not target:
            return await ctx.send("❌ Nie ma kogo przytulić!")

        await ctx.send(
            f"{ctx.author.mention} serdecznie przytula {self.format_random_name(target)} hugg"
        )

    @commands.command()
    async def kiss(self, ctx):
        target = self.random_member(ctx.guild, ctx.author)

        if not target:
            return await ctx.send("❌ Nie ma kogo pocałować!")

        await ctx.send(
            f"{ctx.author.mention} daje buzaka w czółko dla {self.format_random_name(target)} catKISS"
        )

    @commands.command()
    async def myszka(self, ctx):
        target = self.random_member(ctx.guild)

        if not target:
            return

        await ctx.send(
            f"Dzisiejszą myszką zostaje {self.format_random_name(target)} ohCute"
        )

    @commands.command()
    async def ship(self, ctx):
        users = [
            m for m in ctx.guild.members
            if not m.bot
        ]

        if len(users) < 2:
            return await ctx.send("❌ Za mało osób.")

        a, b = random.sample(users, 2)

        percent = random.randint(0, 100)

        await ctx.send(
            f"Ship {self.format_random_name(a)} z {self.format_random_name(b)} ma {percent}% Sure"
        )

    @commands.command(name="60")
    async def sixty(self, ctx):
        target = self.random_member(ctx.guild)

        if target:
            await ctx.send(
                f"Sześćdziesioną dzisiejszego dnia zostaje {self.format_random_name(target)} monkaO"
            )

    @commands.command()
    async def dekiel(self, ctx):
        target = self.random_member(ctx.guild)

        if target:
            await ctx.send(
                f"Deklem dzisiejszego dnia zostaje {self.format_random_name(target)} xdx"
            )

    @commands.command()
    async def aura(self, ctx):
        aura_value = random.randint(-2, 1000)

        await ctx.send(
            f"{ctx.author.mention} ma dzisiaj {aura_value} Aury baseg"
        )

    @commands.command()
    async def iq(self, ctx):
        iq_value = random.randint(1, 200)

        await ctx.send(
            f"{ctx.author.mention} masz {iq_value} iq Nerdge"
        )

    @commands.command()
    async def buu(self, ctx):
        target = self.random_member(ctx.guild, ctx.author)

        if not target:
            return await ctx.send("👻 Nie ma kogo straszyć!")

        await ctx.send(
            f"👻 {ctx.author.mention} straszy {self.format_random_name(target)}! BUUUUU!"
        )

    @commands.command()
    async def fmk(self, ctx):
        users = [
            m for m in ctx.guild.members
            if not m.bot and m != ctx.author
        ]

        if len(users) < 3:
            return await ctx.send(
                "❌ Potrzeba minimum 3 osób!"
            )

        a, b, c = random.sample(users, 3)

        await ctx.send(
            f"fuck - {self.format_random_name(a)} | marry - {self.format_random_name(b)} | kill - {self.format_random_name(c)}"
        )

    @commands.command()
    async def cmd(self, ctx):
        await ctx.send(
            "Dostępne komendy: !test, !hug, !kiss, !myszka, !ship, !60, !dekiel, !aura, !iq, !buu, !fmk, !cmd"
        )


async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))
