# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---------------------------------------------------------

import re
import time

from pyrogram import filters
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from Audify import app
from Audify.mongo.afkdb import add_afk, is_afk, remove_afk
from Audify.mongo.readable_time import get_readable_time


def safe_reason_extract(message: Message) -> str:
    """Safely extract reason text from a command without crashing."""
    if not message.text:
        return ""
    parts = message.text.split(None, 1)
    if len(parts) > 1:
        return parts[1].strip()[:100]
    return ""


@app.on_message(filters.command(["afk"], prefixes=["/"]))
async def active_afk(_, message: Message):
    if message.sender_chat:
        return
    user_id = message.from_user.id
    verifier, reasondb = await is_afk(user_id)
    if verifier:
        await remove_afk(user_id)
        try:
            timeafk = reasondb["time"]
            reasonafk = reasondb.get("reason")
            seenago = get_readable_time((int(time.time() - timeafk)))
            if reasonafk:
                await message.reply_text(
                    f"🔔 {message.from_user.first_name} is back online!\n\nWas away for ⏱️ {seenago}\n\n📝 Reason : {reasonafk}",
                    disable_web_page_preview=True,
                )
            else:
                await message.reply_text(
                    f"🔔🔔 {message.from_user.first_name} is back online!\n\nWas away for ⏱️ {seenago}",
                    disable_web_page_preview=True,
                )
        except Exception:
            await message.reply_text(
                f"🔔 {message.from_user.first_name} is back online!",
                disable_web_page_preview=True,
            )

    # Simplified AFK setting - only text with optional reason
    if len(message.command) == 1:
        details = {"type": "text", "time": time.time(), "data": None, "reason": None}
    else:
        _reason = safe_reason_extract(message)
        details = {
            "type": "text_reason",
            "time": time.time(),
            "data": None,
            "reason": _reason,
        }

    await add_afk(user_id, details)
    await message.reply_text(f"💤 {message.from_user.first_name} is now AFK.\n\nAway from keyboard—be back soon!")


chat_watcher_group = 1


@app.on_message(~filters.me & ~filters.bot & ~filters.via_bot, group=chat_watcher_group)
async def chat_watcher_func(_, message):
    if message.sender_chat or not message.from_user:
        return

    userid = message.from_user.id
    user_name = message.from_user.first_name

    if message.entities:
        possible = ["/afk", f"/afk@{app.username}"]
        message_text = message.text or message.caption or ""
        for entity in message.entities:
            if entity.type == MessageEntityType.BOT_COMMAND:
                command = message_text[entity.offset: entity.offset + entity.length].lower()
                if command in possible:
                    return

    msg = ""
    replied_user_id = 0

    verifier, reasondb = await is_afk(userid)
    if verifier:
        await remove_afk(userid)
        try:
            timeafk = reasondb["time"]
            reasonafk = reasondb.get("reason")
            seenago = get_readable_time((int(time.time() - timeafk)))
            if reasonafk:
                msg += f"🔔 {user_name[:25]} is back online!\n\nWas away for ⏱️ {seenago}\n\n📝 Reason : {reasonafk}\n\n"
            else:
                msg += f"🔔 {user_name[:25]} is back online!\n\nWas away for ⏱️ {seenago}\n\n"
        except:
            msg += f"🔔 {user_name[:25]} is back online!\n\n"

    if message.reply_to_message:
        try:
            replied_first_name = message.reply_to_message.from_user.first_name
            replied_user_id = message.reply_to_message.from_user.id
            verifier, reasondb = await is_afk(replied_user_id)
            if verifier:
                try:
                    timeafk = reasondb["time"]
                    reasonafk = reasondb.get("reason")
                    seenago = get_readable_time((int(time.time() - timeafk)))
                    if reasonafk:
                        msg += f"💤 {replied_first_name[:25]} is AFK.\n\nSince ⏰ {seenago}\n\n📝 Reason : {reasonafk}\n\n"
                    else:
                        msg += f"💤 {replied_first_name[:25]} is AFK.\n\nSince ⏰ {seenago}\n\n"
                except Exception:
                    msg += f"💤 {replied_first_name} is AFK\n\n"
        except:
            pass

    if message.entities:
        entity = message.entities
        j = 0
        for x in range(len(entity)):
            if (entity[j].type) == MessageEntityType.MENTION:
                found = re.findall("@([_0-9a-zA-Z]+)", message.text or "")
                try:
                    get_user = found[j]
                    user = await app.get_users(get_user)
                    if user.id == replied_user_id:
                        j += 1
                        continue
                except:
                    j += 1
                    continue
                verifier, reasondb = await is_afk(user.id)
                if verifier:
                    try:
                        timeafk = reasondb["time"]
                        reasonafk = reasondb.get("reason")
                        seenago = get_readable_time((int(time.time() - timeafk)))
                        if reasonafk:
                            msg += f"💤 {user.first_name[:25]} is AFK.\n\nSince ⏰ {seenago}\n\n📝 Reason : {reasonafk}\n\n"
                        else:
                            msg += f"💤 {user.first_name[:25]} is AFK.\n\nSince ⏰ {seenago}\n\n"
                    except:
                        msg += f"💤 {user.first_name[:25]} is AFK.\n\n"
            elif (entity[j].type) == MessageEntityType.TEXT_MENTION:
                try:
                    user_id = entity[j].user.id
                    if user_id == replied_user_id:
                        j += 1
                        continue
                    first_name = entity[j].user.first_name
                except:
                    j += 1
                    continue
                verifier, reasondb = await is_afk(user_id)
                if verifier:
                    try:
                        timeafk = reasondb["time"]
                        reasonafk = reasondb.get("reason")
                        seenago = get_readable_time((int(time.time() - timeafk)))
                        if reasonafk:
                            msg += f"💤 {first_name[:25]} is AFK.\n\nSince ⏰ {seenago}\n\n📝 Reason : {reasonafk}\n\n"
                        else:
                            msg += f"💤 {first_name[:25]} is AFK.\n\nSince ⏰ {seenago}\n\n"
                    except:
                        msg += f"💤 {first_name[:25]} is AFK.\n\n"
            j += 1
    if msg != "":
        try:
            await message.reply_text(msg, disable_web_page_preview=True)
        except:
            return
