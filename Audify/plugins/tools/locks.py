import re
from pyrogram import filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus
from Audify import app
from Audify.core.mongo import mongodb as db

LOCKDB = db.locks

LOCK_TYPES = {
    "all": None,
    "msg": "can_send_messages",
    "media": "can_send_media_messages",
    "polls": "can_send_polls",
    "invite": "can_invite_users",
    "pin": "can_pin_messages",
    "info": "can_change_info",
    "webprev": "can_add_web_page_previews",
    "inlinebots": "can_use_inline_bots",
    "inline": "can_use_inline_bots",
    "animations": "can_send_animations",
    "games": "can_send_games",
    "stickers": "can_send_stickers",
    "anonchannel": None,
    "forwardall": None,
    "forwardu": None,
    "forwardc": None,
    "links": None,
    "url": None,
    "bot": None,
}

URL_REGEX = re.compile(
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)

async def is_admin_or_approved(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER
        ] and not member.is_restricted
    except:
        return False

@app.on_message(filters.command("locktypes") & filters.group)
async def locktypes_cmd(_, message: Message):
    text = (
        "🔐 Available Lock Types:\n\n"
        "all - Lock everything\n"
        "msg - Lock messages\n"
        "media - Lock photos, videos, etc.\n"
        "polls - Lock polls\n"
        "invite - Prevent adding users\n"
        "pin - Prevent pinning messages\n"
        "info - Prevent changing group info\n"
        "webprev - Disable link previews\n"
        "inlinebots / inline - Prevent using inline bots\n"
        "animations - Lock animations\n"
        "games - Lock games\n"
        "stickers - Lock stickers\n"
        "anonchannel - Prevent sending as channel\n"
        "forwardall - Block all forwarding\n"
        "forwardu - Block forwarding from users\n"
        "forwardc - Block forwarding from channels\n"
        "links / url - Block links\n"
        "bot - Prevent adding bots\n\n"
        "ℹ️ Note: Locks only apply to non-admins and unapproved users."
    )
    await message.reply(text)

async def get_current_locks(chat_id: int):
    data = await LOCKDB.find_one({"chat_id": chat_id})
    return data.get("locks", []) if data else []

@app.on_message(filters.command("locks") & filters.group)
async def view_locks(_, message: Message):
    locks = await get_current_locks(message.chat.id)
    if not locks:
        await message.reply("🔓 No active locks in this chat.")
    else:
        text = "🔐 Active Locks:\n\n" + "\n".join([f"• {x}" for x in locks])
        text += "\n\nℹ️ Locks only apply to non-admins and unapproved users."
        await message.reply(text)

@app.on_message(filters.command("lock") & filters.group)
async def lock_chat(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❓ Usage: /lock media")

    lock_type = message.command[1].lower()
    if lock_type not in LOCK_TYPES:
        return await message.reply("❌ Invalid lock type. Use `/locktypes` to see all options.")

    locks = await get_current_locks(message.chat.id)
    if lock_type in locks:
        return await message.reply(f"🔐 `{lock_type}` is already locked.")

    locks.append(lock_type)
    await LOCKDB.update_one({"chat_id": message.chat.id}, {"$set": {"locks": locks}}, upsert=True)
    await apply_locks(message.chat.id, locks)
    
    if lock_type == "all":
        await message.reply(
            f"🔐 Locked `{lock_type}` for this chat.\n\n"
            "⚠️ **Everything is now locked!**\n"
            "Only admins and approved users can send messages.\n"
            "Non-admins and unapproved users are restricted from all activities."
        )
    else:
        await message.reply(
            f"🔐 Locked `{lock_type}` for this chat.\n"
            "ℹ️ This lock only applies to non-admins and unapproved users."
        )

@app.on_message(filters.command("unlock") & filters.group)
async def unlock_chat(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❓ Usage: /unlock media")

    lock_type = message.command[1].lower()
    if lock_type not in LOCK_TYPES:
        return await message.reply("❌ Invalid lock type. Use `/locktypes` to see all options.")

    locks = await get_current_locks(message.chat.id)
    if lock_type not in locks:
        return await message.reply(f"🔓 `{lock_type}` is already unlocked.")

    locks.remove(lock_type)
    await LOCKDB.update_one({"chat_id": message.chat.id}, {"$set": {"locks": locks}}, upsert=True)
    await apply_locks(message.chat.id, locks)
    
    if lock_type == "all":
        await message.reply(
            f"🔓 Unlocked `{lock_type}` for this chat.\n\n"
            "✅ **All restrictions have been removed!**\n"
            "Everyone can now participate normally in the group."
        )
    else:
        await message.reply(f"🔓 Unlocked `{lock_type}` for this chat.")

async def apply_locks(chat_id: int, locks: list):
    if "all" in locks:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_change_info=False,
            can_add_web_page_previews=False,
            can_use_inline_bots=False,
            can_send_animations=False,
            can_send_games=False,
            can_send_stickers=False,
        )
        await app.set_chat_permissions(chat_id, permissions=permissions)
        return

    permissions = ChatPermissions(
        can_send_messages="msg" not in locks,
        can_send_media_messages="media" not in locks,
        can_send_polls="polls" not in locks,
        can_invite_users="invite" not in locks,
        can_pin_messages="pin" not in locks,
        can_change_info="info" not in locks,
        can_add_web_page_previews="webprev" not in locks,
        can_use_inline_bots="inlinebots" not in locks and "inline" not in locks,
        can_send_animations="animations" not in locks,
        can_send_games="games" not in locks,
        can_send_stickers="stickers" not in locks,
    )
    await app.set_chat_permissions(chat_id, permissions=permissions)

def has_urls(text: str) -> bool:
    if not text:
        return False
    return bool(URL_REGEX.search(text)) or any(
        word.startswith(("http://", "https://", "www.", "t.me/", "telegram.me/"))
        for word in text.split()
    )

@app.on_message(filters.group & ~filters.command(["lock", "unlock", "locks", "locktypes"]))
async def handle_custom_locks(_, message: Message):
    try:
        if not message.from_user:
            return
            
        locks = await get_current_locks(message.chat.id)
        if not locks:
            return

        is_admin = await is_admin_or_approved(message.chat.id, message.from_user.id)
        if is_admin:
            return

        should_delete = False
        delete_reason = ""

        if "all" in locks:
            should_delete = True
            delete_reason = "All messages are locked for non-admins"

        elif message.forward_date:
            if "forwardall" in locks:
                should_delete = True
                delete_reason = "All forwarding is locked"
            elif "forwardu" in locks and message.forward_from:
                should_delete = True
                delete_reason = "User forwarding is locked"
            elif "forwardc" in locks and message.forward_from_chat:
                should_delete = True
                delete_reason = "Channel forwarding is locked"

        elif message.sender_chat and "anonchannel" in locks:
            should_delete = True
            delete_reason = "Anonymous channel posting is locked"

        elif message.text and ("links" in locks or "url" in locks):
            if has_urls(message.text):
                should_delete = True
                delete_reason = "Links are locked"

        elif message.caption and ("links" in locks or "url" in locks):
            if has_urls(message.caption):
                should_delete = True
                delete_reason = "Links are locked"

        if should_delete:
            await message.delete()
            
    except Exception as e:
        print(f"Lock handler error: {e}")

@app.on_message(filters.new_chat_members & filters.group)
async def handle_new_members(_, message: Message):
    try:
        locks = await get_current_locks(message.chat.id)
        if "bot" in locks or "all" in locks:
            for user in message.new_chat_members:
                if user.is_bot:
                    try:
                        await app.ban_chat_member(message.chat.id, user.id)
                        await app.unban_chat_member(message.chat.id, user.id)
                        await message.delete()
                        break
                    except Exception as e:
                        print(f"Bot removal error: {e}")
    except Exception as e:
        print(f"New member handler error: {e}")
