from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message

from Audify import app
from Audify.core.call import Audify
from Audify.utils import bot_sys_stats
from Audify.utils.decorators.language import language
from Audify.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL


@app.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()

    # Send initial message (photo or text depending on config)
    if PING_IMG_URL:
        response = await message.reply_photo(
            photo=PING_IMG_URL,
            caption=_["ping_1"].format(app.mention),
        )
    else:
        response = await message.reply_text(
            text=_["ping_1"].format(app.mention),
        )

    pytgping = await Audify.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000

    # Edit accordingly
    if PING_IMG_URL:
        await response.edit_caption(
            caption=_["ping_2"].format(resp, app.mention, UP, RAM, CPU, DISK, pytgping),
            reply_markup=supp_markup(_),
        )
    else:
        await response.edit_text(
            text=_["ping_2"].format(resp, app.mention, UP, RAM, CPU, DISK, pytgping),
            reply_markup=supp_markup(_),
        )
