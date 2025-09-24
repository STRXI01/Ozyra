# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---------------------------------------------------------

from pyrogram.enums import ParseMode
from Audify import app
from Audify.utils.database import is_on_off
from config import LOGGER_ID


async def play_logs(message, streamtype):
    if await is_on_off(2):
        # Safely get query text
        if message.text:
            parts = message.text.split(None, 1)
            query = parts[1] if len(parts) > 1 else "No query provided"
        else:
            query = "No query provided"

        logger_text = f"""
<b>🎧 Audify Play Log</b>

<b>📍 Chat Info</b>
├ ID: <code>{message.chat.id}</code>
├ Title: {message.chat.title}
└ Username: @{message.chat.username if message.chat.username else 'N/A'}

<b>🙋‍♂️ User Info</b>
├ ID: <code>{message.from_user.id}</code>
├ Name: {message.from_user.mention}
└ Username: @{message.from_user.username if message.from_user.username else 'N/A'}

<b>🎵 Playback Info</b>
├ Query: <code>{query}</code>
└ Stream Type: <code>{streamtype}</code>
"""
        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except Exception:
                pass
