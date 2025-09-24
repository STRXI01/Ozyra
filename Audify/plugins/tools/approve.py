# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---------------------------------------------------------

from pyrogram import filters
from pyrogram.types import Message
from Audify import app
from Audify.utils.database import authuserdb
from Audify.utils.Audify_BAN import admin_filter


# ========== Database Helpers ==========

async def get_approved_users(chat_id: int):
    chat = await authuserdb.find_one({"chat_id": chat_id})
    return chat.get("approved_users", []) if chat else []


async def is_user_approved(chat_id: int, user_id: int):
    users = await get_approved_users(chat_id)
    return user_id in users


async def approve_user(chat_id: int, user_id: int):
    await authuserdb.update_one(
        {"chat_id": chat_id},
        {"$addToSet": {"approved_users": user_id}},
        upsert=True,
    )


async def unapprove_user(chat_id: int, user_id: int):
    await authuserdb.update_one(
        {"chat_id": chat_id},
        {"$pull": {"approved_users": user_id}},
        upsert=True,
    )


async def clear_all_approvals(chat_id: int):
    await authuserdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"approved_users": []}},
        upsert=True,
    )


# ========== Commands ==========

# /approval -> Check approval status
@app.on_message(filters.command("approval"))
async def approval_status(_, message: Message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    status = await is_user_approved(message.chat.id, user.id)
    if status:
        await message.reply(f"✅ [User](tg://user?id={user.id}) is approved in this chat.")
    else:
        await message.reply(f"❌ [User](tg://user?id={user.id}) is NOT approved in this chat.")


# /approve -> Approve user
@app.on_message(filters.command("approve") & admin_filter)
async def approve_cmd(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("❗ Reply to a user to approve them.")
    user = message.reply_to_message.from_user
    await approve_user(message.chat.id, user.id)
    await message.reply(f"✅ [User](tg://user?id={user.id}) has been approved.")


# /unapprove -> Unapprove user
@app.on_message(filters.command("unapprove") & admin_filter)
async def unapprove_cmd(_, message: Message):
    if not message.reply_to_message:
        return await message.reply("❗ Reply to a user to unapprove them.")
    user = message.reply_to_message.from_user
    await unapprove_user(message.chat.id, user.id)
    await message.reply(f"❌ [User](tg://user?id={user.id}) has been unapproved.")


# /approved -> List all approved users
@app.on_message(filters.command("approved") & admin_filter)
async def approved_list(_, message: Message):
    users = await get_approved_users(message.chat.id)
    if not users:
        return await message.reply("ℹ️ No approved users in this chat.")
    text = "✅ **Approved users in this chat:**\n\n"
    for i, user_id in enumerate(users, 1):
        text += f"{i}. [User](tg://user?id={user_id})\n"
    await message.reply(text)


# /unapproveall -> Remove all approvals
@app.on_message(filters.command("unapproveall") & admin_filter)
async def unapprove_all(_, message: Message):
    await clear_all_approvals(message.chat.id)
    await message.reply("⚠️ All users have been unapproved in this chat.")
