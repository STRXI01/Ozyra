import config
import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall


from Audify import LOGGER, app, userbot
from Audify.core.call import Audify
from Audify.misc import sudo
from Audify.plugins import ALL_MODULES
from Audify.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS
from Audify.utils.cookies import fetch_and_store_cookies   #  Import cookies


async def init():
    #  Ensuring cookies are available/updated each time before starting bot
    try:
        await fetch_and_store_cookies()
        LOGGER("Audify").info("🍪 Cookies loaded successfully.")
    except Exception as e:
        LOGGER("Audify").error(f"🚫 Failed to initialize cookies: {e}")
        exit()

    # String session checker
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("🚫 String Session Missing! Please configure at least one Pyrogram session string.")
        exit()

    # Load banned users
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass

    #  Start clients
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("Audify.plugins" + all_module)
    LOGGER("Audify.plugins").info("✅ All modules successfully loaded🎶.")
    await userbot.start()
    await Audify.start()

    # Test streaming
    try:
        await Audify.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("Audify").error(
            "📢 Please start a voice chat in your log group or linked channel!\n\n⚠️ Kawai cannot stream without an active group call."
        )
        exit()
    except:
        pass

    # ✅ Register decorators and keep alive
    await Audify.decorators()
    LOGGER("Audify").info(
        "🎧Kawai Music started successfully.\n🛡️ An @Alpha_Botz project®"
    )
    await idle()

    # ✅ Stop clients on exit
    await app.stop()
    await userbot.stop()
    LOGGER("Audify").info("🛑 Music Bot has stopped. See you soon! 👋")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
