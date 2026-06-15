import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
import asyncio

class WrongChannelError(commands.CheckFailure):
    pass

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DiscordBot")

# Load environment
load_dotenv("config.env")
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID_RAW = os.getenv("OWNER_ID")
BETA_TESTER_ROLE_ID_RAW = os.getenv("BETA_TESTER_ROLE_ID")
ALLOWED_CHANNEL_IDS_RAW = os.getenv("ALLOWED_CHANNEL_IDS")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "505na")
TWITCH_POLL_INTERVAL = int(os.getenv("TWITCH_POLL_INTERVAL", "180"))

if not TOKEN:
    raise ValueError("Brak DISCORD_TOKEN w pliku config.env")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Zmienna do śledzenia trybu dostępu (True = tylko beta testerzy, False = dostęp publiczny)
BETA_MODE_ENABLED = True

# Register extensions before connecting
async def _setup_hook():
    try:
        await bot.load_extension('cogs.general')
        logger.info("Załadowano extension cogs.general w setup_hook")
    except Exception as e:
        logger.error(f"Błąd podczas ładowania extension cogs.general w setup_hook: {e}")

bot.setup_hook = _setup_hook

# Ready event: fetch owner and register owner-only check if configured
OWNER_ID = None
BETA_TESTER_ROLE_ID = None
ALLOWED_CHANNEL_IDS = None
if OWNER_ID_RAW:
    try:
        OWNER_ID = int(OWNER_ID_RAW)
    except ValueError:
        logger.warning("OWNER_ID w config.env nie jest liczbą; spróbuję pobrać właściciela z application info.")
if BETA_TESTER_ROLE_ID_RAW:
    try:
        BETA_TESTER_ROLE_ID = int(BETA_TESTER_ROLE_ID_RAW)
    except ValueError:
        logger.warning("BETA_TESTER_ROLE_ID w config.env nie jest liczbą.")
if ALLOWED_CHANNEL_IDS_RAW:
    try:
        ALLOWED_CHANNEL_IDS = [int(x.strip()) for x in ALLOWED_CHANNEL_IDS_RAW.split(",") if x.strip()]
    except ValueError:
        logger.warning("ALLOWED_CHANNEL_IDS w config.env musi zawierać tylko liczby oddzielone przecinkami.")

@bot.event
async def on_ready():
    global OWNER_ID
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

    if OWNER_ID is None:
        try:
            app_info = await bot.application_info()
            OWNER_ID = app_info.owner.id
            logger.info(f"Ustawiono OWNER_ID na {OWNER_ID} (pobrano z application info)")
        except Exception as e:
            logger.warning(f"Nie udało się pobrać application_info(): {e}")

    if OWNER_ID is not None:
        def _has_access(ctx):
            if ALLOWED_CHANNEL_IDS is not None and ctx.channel.id not in ALLOWED_CHANNEL_IDS:
                raise WrongChannelError("wrong channel")
            if ctx.author.id == OWNER_ID:
                return True
            # Jeśli tryb beta jest włączony, sprawdź rolę beta testera
            if BETA_MODE_ENABLED:
                if BETA_TESTER_ROLE_ID is not None:
                    for role in ctx.author.roles:
                        if role.id == BETA_TESTER_ROLE_ID:
                            return True
                return False
            else:
                # Jeśli tryb beta jest wyłączony, pozwól dostęp wszystkim
                return True

        bot.check(_has_access)
        if BETA_TESTER_ROLE_ID is not None:
            logger.info(f"Zarejestrowano ograniczenie komend dla właściciela, roli ID {BETA_TESTER_ROLE_ID} i kanałów {ALLOWED_CHANNEL_IDS}.")
        else:
            logger.info(f"Zarejestrowano ograniczenie komend tylko dla właściciela: {OWNER_ID} i kanałów {ALLOWED_CHANNEL_IDS}.")

    # Debug: list registered commands
    cmd_names = sorted(c.name for c in bot.commands)
    logger.info(f"Zarejestrowane komendy: {cmd_names}")

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
        await ctx.send("Zły kanał, spróbuj na <#1035107360777175041>")
    elif isinstance(error, commands.NotOwner):
        await ctx.send("❌Nie masz uprawnień do użycia tej komendy.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Nie masz uprawnień do użycia tej komendy.")
    else:
        raise error

# Run
if __name__ == '__main__':
    bot.run(TOKEN)
