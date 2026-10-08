import os
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
import asyncio

# Keep extension imports of `botd` bound to this instance when started as a script.
sys.modules.setdefault("botd", sys.modules[__name__])

class WrongChannelError(commands.CheckFailure):
    pass

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DiscordBot")

# Load environment
load_dotenv("config.env")
TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_CHANNEL_IDS_RAW = os.getenv("ALLOWED_CHANNEL_IDS")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "505na")
TWITCH_POLL_INTERVAL = int(os.getenv("TWITCH_POLL_INTERVAL", "180"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "1035112319065268275"))

if not TOKEN:
    raise ValueError("Brak DISCORD_TOKEN w pliku config.env")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Ustawienia dostępu można nadpisywać osobno dla każdego serwera.
@dataclass
class GuildSettings:
    allowed_channel_ids: list[int] | None = None
    log_channel_id: int | None = None


def _guild_env_value(guild_id: int, setting: str) -> str | None:
    return os.getenv(f"GUILD_{guild_id}_{setting}")


def _parse_guild_int(guild_id: int, setting: str) -> int | None:
    value = _guild_env_value(guild_id, setting)
    if value is None or not value.strip():
        return None
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"GUILD_{guild_id}_{setting} musi być liczbą.") from error


def _parse_guild_channel_ids(guild_id: int) -> list[int] | None:
    setting = "ALLOWED_CHANNEL_IDS"
    value = _guild_env_value(guild_id, setting)
    if value is None or not value.strip():
        return None
    if value.strip().lower() == "all":
        return []
    try:
        return [int(channel_id.strip()) for channel_id in value.split(",") if channel_id.strip()]
    except ValueError as error:
        raise ValueError(
            f"GUILD_{guild_id}_{setting} musi zawierać liczby oddzielone przecinkami lub all."
        ) from error


def _load_guild_settings() -> dict[int, GuildSettings]:
    setting_pattern = re.compile(
        r"^GUILD_(\d+)_(?:ALLOWED_CHANNEL_IDS|LOG_CHANNEL_ID)$"
    )
    guild_ids = {
        int(match.group(1))
        for name in os.environ
        if (match := setting_pattern.fullmatch(name))
    }
    return {
        guild_id: GuildSettings(
            allowed_channel_ids=_parse_guild_channel_ids(guild_id),
            log_channel_id=_parse_guild_int(guild_id, "LOG_CHANNEL_ID"),
        )
        for guild_id in guild_ids
    }


GUILD_SETTINGS = _load_guild_settings()


def get_guild_settings(guild_id: int | None) -> GuildSettings:
    configured = GUILD_SETTINGS.get(guild_id) if guild_id is not None else None
    return GuildSettings(
        allowed_channel_ids=(
            configured.allowed_channel_ids
            if configured and configured.allowed_channel_ids is not None
            else ALLOWED_CHANNEL_IDS
        ),
        log_channel_id=(
            configured.log_channel_id
            if configured and configured.log_channel_id is not None
            else LOG_CHANNEL_ID
        ),
    )


async def _has_guild_access(ctx: commands.Context) -> bool:
    settings = get_guild_settings(ctx.guild.id if ctx.guild else None)
    if settings.allowed_channel_ids and ctx.channel.id not in settings.allowed_channel_ids:
        channels = ", ".join(f"<#{channel_id}>" for channel_id in settings.allowed_channel_ids)
        raise WrongChannelError(f"Zły kanał, spróbuj na {channels}")
    return True


bot.check(_has_guild_access)

# Register extensions before connecting
async def _setup_hook():
    try:
        await bot.load_extension('cogs.general')
        logger.info("Załadowano extension cogs.general w setup_hook")
    except Exception as e:
        logger.error(f"Błąd podczas ładowania extension cogs.general w setup_hook: {e}")

    server_cogs_dir = Path(__file__).parent / "cogs" / "servers"
    for cog_path in sorted(server_cogs_dir.glob("guild_*.py")):
        if not cog_path.stem.isidentifier():
            logger.warning("Pomijam plik z nieprawidłową nazwą modułu: %s", cog_path.name)
            continue
        extension = f"cogs.servers.{cog_path.stem}"
        await bot.load_extension(extension)
        logger.info("Załadowano moduł serwera %s", cog_path.stem.removeprefix("guild_"))

bot.setup_hook = _setup_hook

# Ready event: log bot status and load shared access configuration.
ALLOWED_CHANNEL_IDS = None
if ALLOWED_CHANNEL_IDS_RAW:
    try:
        ALLOWED_CHANNEL_IDS = [int(x.strip()) for x in ALLOWED_CHANNEL_IDS_RAW.split(",") if x.strip()]
    except ValueError:
        logger.warning("ALLOWED_CHANNEL_IDS w config.env musi zawierać tylko liczby oddzielone przecinkami.")

@bot.event
async def on_ready():
    logger.info(f"Zalogowano jako {bot.user}")

    # Jeśli podano dane Twitch w env, uruchom pętlę aktualizującą status bota z danych kanału
    if TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET:
        # Inicjalizuj licznik pętli (w pamięci, zeruje się po restarcie)
        bot.twitch_loop_counter = 0
        async def twitch_status_loop():
            async with aiohttp.ClientSession() as session:
                while True:
                    # Zwiększ licznik iteracji pętli
                    try:
                        bot.twitch_loop_counter += 1
                    except Exception:
                        bot.twitch_loop_counter = getattr(bot, 'twitch_loop_counter', 0) + 1
                    logger.info(f"Twitch loop iteration: {bot.twitch_loop_counter}")
                    try:
                        # Pobierz app access token
                        token_url = "https://id.twitch.tv/oauth2/token"
                        params = {
                            "client_id": TWITCH_CLIENT_ID,
                            "client_secret": TWITCH_CLIENT_SECRET,
                            "grant_type": "client_credentials",
                        }
                        async with session.post(token_url, params=params) as r:
                            token_data = await r.json()
                        access_token = token_data.get("access_token")

                        headers = {"Client-ID": TWITCH_CLIENT_ID, "Authorization": f"Bearer {access_token}"}

                        # Pobierz użytkownika aby dostać id i follower count
                        users_url = f"https://api.twitch.tv/helix/users?login={TWITCH_CHANNEL}"
                        async with session.get(users_url, headers=headers) as r:
                            users_data = await r.json()

                        user = None
                        if users_data and users_data.get("data"):
                            user = users_data["data"][0]
                        else:
                            logger.warning(f"Brak danych użytkownika dla {TWITCH_CHANNEL}: {users_data}")

                        followers = None
                        user_id = None
                        if user:
                            user_id = user.get("id")
                            logger.info(f"Pobrany user_id dla {TWITCH_CHANNEL}: {user_id}")
                            # Pobierz liczbę followerów kanału
                            followers_url = f"https://api.twitch.tv/helix/channels/followers?broadcaster_id={user_id}&first=1"
                            async with session.get(followers_url, headers=headers) as r:
                                followers_data = await r.json()
                            logger.info(f"Followers API response: {followers_data}")
                            if followers_data and followers_data.get("total") is not None:
                                followers = followers_data.get("total")
                                logger.info(f"Pobrania followers dla {TWITCH_CHANNEL}: {followers}")
                            else:
                                logger.warning(f"Brak follower_count z followers API: {followers_data}")
                        else:
                            logger.warning(f"User object jest None dla {TWITCH_CHANNEL}")

                        # Pobierz stream (czy jest live)
                        streams_url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_CHANNEL}"
                        async with session.get(streams_url, headers=headers) as r:
                            streams_data = await r.json()

                        stream = None
                        if streams_data and streams_data.get("data"):
                            data = streams_data["data"]
                            if len(data) > 0:
                                stream = data[0]

                        # Format: LIVE ON/OFF | Followers: X
                        status_prefix = "LIVE ON" if stream else "LIVE OFF"
                        follow_text = f"Followers: {followers}" if followers is not None else "Followers: ?"
                        status_text = f"{status_prefix} | {follow_text}"

                        if stream:
                            await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(name=status_text, url=f"https://twitch.tv/{TWITCH_CHANNEL}"))
                            logger.info(f"Ustawiono status STREAMING (live) z Twitch: {status_text}")
                        else:
                            await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(name=status_text, url=f"https://twitch.tv/{TWITCH_CHANNEL}"))
                            logger.info(f"Kanał Twitch jest offline — ustawiono status STREAMING: {status_text}")
                    except Exception as e:
                        logger.warning(f"Błąd podczas pobierania danych Twitch: {e}")

                    await asyncio.sleep(TWITCH_POLL_INTERVAL)

        bot.loop.create_task(twitch_status_loop())
        logger.info("Uruchomiono pętlę aktualizacji statusu z Twitch.")

    logger.info(
        "Zarejestrowano ograniczenia kanałów z konfiguracją serwerową "
        "dla %s serwerów.",
        len(GUILD_SETTINGS),
    )

    # Debug: list registered commands
    cmd_names = sorted(c.name for c in bot.commands)
    logger.info(f"Zarejestrowane komendy: {cmd_names}")

def get_log_channel(guild):
    if guild is None:
        return None
    log_channel_id = get_guild_settings(guild.id).log_channel_id
    if log_channel_id is None:
        return None
    channel = guild.get_channel(log_channel_id)
    if isinstance(channel, discord.TextChannel):
        return channel
    return None


async def _format_account_age(created_at):
    age_days = max(int((discord.utils.utcnow() - created_at).total_seconds() // 86400), 0)
    years, remaining_days = divmod(age_days, 365)
    months, days = divmod(remaining_days, 30)

    if years:
        parts = [
            f"{years} year{'s' if years != 1 else ''}",
            f"{months} month{'s' if months != 1 else ''}",
            f"{days} day{'s' if days != 1 else ''}",
        ]
    elif months:
        parts = [
            f"{months} month{'s' if months != 1 else ''}",
            f"{days} day{'s' if days != 1 else ''}",
        ]
    else:
        parts = [f"{days} day{'s' if days != 1 else ''}"]

    return ", ".join(parts)


@bot.event
async def on_member_join(member):
    log_channel = get_log_channel(member.guild)
    if log_channel is None:
        return

    created_at = member.created_at
    age_text = await _format_account_age(created_at)
    joined_at = member.joined_at or discord.utils.utcnow()

    embed = discord.Embed(
        description=(
            f"@{member.name} {member.display_name}\n\n"
            f"**Account Age**\n"
            f"{age_text}\n\n"
            f"**ID:** {member.id}"
        ),
        color=discord.Color.from_rgb(15, 16, 19),
        timestamp=joined_at,
    )
    embed.color = discord.Color.from_rgb(76, 175, 80)
    embed.set_author(
        name="Member Joined",
        icon_url="https://cdn.discordapp.com/emojis/1374002125509664829.png",
    )
    embed.set_footer(text=f"Dołączenie: {joined_at.strftime('%d.%m.%Y %H:%M:%S')}")
    await log_channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
    log_channel = get_log_channel(member.guild)
    if log_channel is None:
        return

    left_at = discord.utils.utcnow()
    embed = discord.Embed(
        description=(
            f"@{member.name} {member.display_name}\n\n"
            f"**ID:** {member.id}"
        ),
        color=discord.Color.from_rgb(15, 16, 19),
        timestamp=left_at,
    )
    embed.color = discord.Color.from_rgb(255, 82, 82)
    embed.set_author(
        name="Member Left",
        icon_url="https://cdn.discordapp.com/emojis/1374002125509664829.png",
    )
    embed.set_footer(text=f"Wyjście: {left_at.strftime('%d.%m.%Y %H:%M:%S')}")
    await log_channel.send(embed=embed)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    goodnight_variants = ["dobranoc", "dombranoc"]
    if any(variant in content for variant in goodnight_variants):
        emoji = None
        if message.guild:
            emoji = discord.utils.get(message.guild.emojis, name="peppo_heart")
        if emoji is not None:
            await message.channel.send(f"Dobranoc {emoji}")
        else:
            await message.channel.send("Dobranoc")

    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, WrongChannelError):
        await ctx.send(str(error))
    elif isinstance(error, commands.NotOwner):
        await ctx.send("❌Nie masz uprawnień do użycia tej komendy.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Nie masz uprawnień do użycia tej komendy.")
    else:
        raise error

async def discord_available() -> bool:
    """Sprawdza, czy Discord jest dostępny przez API gateway z krótkim timeoutem."""
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("https://discord.com/api/v10/gateway") as response:
                return response.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as error:
        logger.warning("Discord jest niedostępny: %s", error)
        return False


async def run_bot() -> None:
    retry_delay = 10

    while True:
        if not await discord_available():
            logger.warning("Brak dostępu do Discorda. Ponawiam sprawdzenie za %s sekund...", retry_delay)
            await asyncio.sleep(retry_delay)
            continue

        try:
            logger.info("Internet działa. Łączenie z Discordem...")
            await bot.start(TOKEN, reconnect=True)
            logger.info("Połączenie bota zostało zamknięte. Ponawiam za %s sekund...", retry_delay)
        except (aiohttp.ClientError, OSError, asyncio.TimeoutError) as error:
            logger.warning("Błąd połączenia z Discordem: %s. Ponawiam za %s sekund...", error, retry_delay)
        except discord.LoginFailure:
            logger.critical(
                "Logowanie do Discorda nie powiodło się. Sprawdź, czy DISCORD_TOKEN "
                "w pliku config.env jest poprawnym tokenem bota."
            )
            raise
        except asyncio.CancelledError:
            logger.info("Zatrzymywanie bota...")
            raise
        except Exception:
            logger.exception("Nieoczekiwany błąd. Ponawiam za %s sekund...", retry_delay)
        finally:
            try:
                await bot.close()
            except Exception:
                logger.debug("Błąd podczas zamykania klienta.", exc_info=True)

        await asyncio.sleep(retry_delay)


if __name__ == '__main__':
    asyncio.run(run_bot())
