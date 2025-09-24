from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from Audify import app
from Audify.core.call import Audify
from Audify.utils import bot_sys_stats
from Audify.utils.decorators.language import language
from Audify.utils.inline import supp_markup
from config import BANNED_USERS
import asyncio

@app.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    
    pytgping, stats, response = await asyncio.gather(
        Audify.ping(),
        bot_sys_stats(),
        message.reply_text(
            _["ping_1"].format(app.mention),
        )
    )
    
    UP, CPU, RAM, DISK = stats
    resp = (datetime.now() - start).microseconds / 10000
    
    await response.edit_text(
        _["ping_2"].format(resp, app.mention, UP),
        reply_markup=supp_markup(_),
    )
