# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---------------------------------------------------------

from asyncio import sleep
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.errors import MessageDeleteForbidden, RPCError
from pyrogram.types import Message
from Audify.utils.Audify_BAN import admin_filter
from Audify import app


def divide_chunks(data, size=100):
    """Yield successive n-sized chunks from data."""
    for i in range(0, len(data), size):
        yield data[i : i + size]


async def safe_delete_messages(app, chat_id, message_ids):
    """Delete messages in batches safely with error handling."""
    grouped_ids = list(divide_chunks(message_ids))
    deleted_count = 0

    for batch in grouped_ids:
        try:
            await app.delete_messages(chat_id=chat_id, message_ids=batch, revoke=True)
            deleted_count += len(batch)
        except MessageDeleteForbidden:
            # Skip messages we can't delete
            continue
        except RPCError:
            continue

    return deleted_count


@app.on_message(filters.command("purge") & filters.group & admin_filter)
async def purge_messages(app, message: Message):
    if message.chat.type != ChatType.SUPERGROUP:
        return await message.reply_text(
            "⚠️ I can't purge messages in a basic group. Please upgrade to a supergroup."
        )

    if not message.reply_to_message:
        return await message.reply_text("✏️ Reply to a message to start purging from there.")

    message_ids = list(range(message.reply_to_message.id, message.id + 1))

    deleted_count = await safe_delete_messages(app, message.chat.id, message_ids)

    try:
        await message.delete()
    except MessageDeleteForbidden:
        pass

    confirmation = await message.reply_text(f"✅ Successfully deleted {deleted_count} messages.")
    await sleep(3)
    try:
        await confirmation.delete()
    except MessageDeleteForbidden:
        pass


@app.on_message(filters.command("spurge") & filters.group & admin_filter)
async def silent_purge(app, message: Message):
    """Same as purge, but without sending confirmation."""
    if message.chat.type != ChatType.SUPERGROUP:
        return await message.reply_text(
            "⚠️ I can't purge messages in a basic group. Please upgrade to a supergroup."
        )

    if not message.reply_to_message:
        return await message.reply_text("✏️ Reply to a message to start silent purging.")

    message_ids = list(range(message.reply_to_message.id, message.id + 1))

    await safe_delete_messages(app, message.chat.id, message_ids)

    try:
        await message.delete()
    except MessageDeleteForbidden:
        pass


@app.on_message(filters.command("del") & filters.group & admin_filter)
async def delete_single_message(app, message: Message):
    if message.chat.type != ChatType.SUPERGROUP:
        return await message.reply_text(
            "⚠️ I can't delete messages in a basic group. Please upgrade to a supergroup."
        )

    if not message.reply_to_message:
        return await message.reply_text("✏️ Reply to the message you want me to delete.")

    try:
        await message.delete()
    except MessageDeleteForbidden:
        pass

    try:
        await app.delete_messages(chat_id=message.chat.id, message_ids=message.reply_to_message.id)
    except MessageDeleteForbidden:
        await message.reply_text("🚫 Unable to delete this message. I may lack permissions.")
