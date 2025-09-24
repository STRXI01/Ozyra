# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---------------------------------------------------------

import asyncio
from pyrogram.enums import ChatType
from Audify import app
from pyrogram import filters
from Audify.utils.Audify_BAN import admin_filter
from pyrogram.errors import FloodWait

SPAM_CHATS = []

@app.on_message(filters.command(["mention", "all"]) & filters.group & admin_filter)
async def tag_all_users(_, message):
    replied = message.reply_to_message

    # No text or reply provided
    if len(message.command) < 2 and not replied:
        await message.reply_text("✨ **Please reply to a message or provide some text to mention everyone.**")
        return

    chat_id = message.chat.id
    SPAM_CHATS.append(chat_id)
    usertxt = ""
    batch_count = 0

    # Determine the message to send
    text = replied.text if replied else message.text.split(None, 1)[1]

    async for member in app.get_chat_members(chat_id):
        # Stop if process was canceled
        if chat_id not in SPAM_CHATS:
            break

        # Skip bots
        if member.user.is_bot:
            continue

        usertxt += f"\n🔹 [{member.user.first_name}](tg://user?id={member.user.id})"
        batch_count += 1

        # Send in batches of 5
        if batch_count == 5:
            try:
                await app.send_message(chat_id, f"{text}\n{usertxt}")
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await app.send_message(chat_id, f"{text}\n{usertxt}")
            await asyncio.sleep(2)  # Small delay to avoid flood
            usertxt = ""
            batch_count = 0

    # Send remaining mentions if any
    if usertxt and chat_id in SPAM_CHATS:
        try:
            await app.send_message(chat_id, f"{text}\n{usertxt}")
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await app.send_message(chat_id, f"{text}\n{usertxt}")

    # Cleanup
    if chat_id in SPAM_CHATS:
        SPAM_CHATS.remove(chat_id)

@app.on_message(filters.command("alloff") & ~filters.private)
async def cancelcmd(_, message):
    chat_id = message.chat.id
    if chat_id in SPAM_CHATS:
        SPAM_CHATS.remove(chat_id)
        await message.reply_text("✅ **Tagging process has been successfully stopped.**")
    else:
        await message.reply_text("⚠️ **No active tagging process is currently running.**")
