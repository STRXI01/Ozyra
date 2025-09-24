# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---------------------------------------------------------

import datetime
from pyrogram import filters, enums
from pyrogram.types import ChatPermissions
from pyrogram.errors.exceptions.bad_request_400 import (
    ChatAdminRequired,
    UserAdminInvalid
)
from Audify import app


# ---------------------- Utils ----------------------
def mention(user_id, name, tg_mention=True):
    return f"[{name}](tg://user?id={user_id})" if tg_mention else f"[{name}](https://t.me/{user_id})"


async def get_userid_from_username(username):
    try:
        user = await app.get_users(username)
        return [user.id, user.first_name]
    except Exception:
        return None


def ensure_sender(message):
    """Ensure message has a valid from_user and is not from an anonymous admin."""
    if not message.from_user:
        return "❌ Cannot identify sender. This might be from an anonymous admin or channel."
    return None


def ensure_admin_privileges(member, action: str):
    """Check if the human admin has the required privileges (restrict)."""
    if member.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        if getattr(member.privileges, "can_restrict_members", False):
            return None
        return f"⚠️ You don't have permission to {action} members."
    return f"⚠️ You don't have permission to {action} members."


async def ensure_bot_privileges(chat, action: str):
    """Check if the bot can restrict/ban members."""
    bot_id = (await app.get_me()).id
    bot_member = await chat.get_member(bot_id)

    if bot_member.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return f"❌ I must be an admin to {action} members."

    # can_restrict_members covers ban/mute/unmute/unban in groups/supergroups
    if not getattr(bot_member.privileges, "can_restrict_members", False):
        return f"❌ I need 'Ban/Restrict Members' permission to {action} members."

    return None


async def ensure_target_valid(chat, target_id: int):
    """
    Ensure target is valid to act on:
    - not the chat creator or an admin
    - not the bot itself
    """
    # Prevent acting on the bot
    bot_id = (await app.get_me()).id
    if target_id == bot_id:
        return "🙃 I won't act on myself."

    try:
        target_member = await chat.get_member(target_id)
    except Exception:
        # If user is not found in chat, allow for ban/unban paths to handle
        return None

    if target_member.status == enums.ChatMemberStatus.OWNER:
        return "👑 I can't act on the chat owner."

    if target_member.status == enums.ChatMemberStatus.ADMINISTRATOR:
        return "🛡️ I won't act on an admin."

    return None


# ---------------------- Core Actions ----------------------
async def ban_user(user_id, first_name, admin_id, admin_name, chat_id, reason=None, time=None):
    try:
        await app.ban_chat_member(chat_id, user_id)
    except ChatAdminRequired:
        return "🚫 I need ban permissions to execute this action.", False
    except UserAdminInvalid:
        return "❌ I can't ban an admin.", False
    except Exception as e:
        bot_id = (await app.get_me()).id
        if user_id == bot_id:
            return "🙄 I'm not going to ban myself.", False
        return f"🚫 Oops!\n{e}", False

    msg_text = f"🚫 {mention(user_id, first_name)} was banned by {mention(admin_id, admin_name)}\n"
    if reason:
        msg_text += f"📌 Reason: `{reason}`\n"
    if time:
        msg_text += f"⏰ Duration: `{time}`\n"
    return msg_text, True


async def unban_user(user_id, first_name, admin_id, admin_name, chat_id):
    try:
        await app.unban_chat_member(chat_id, user_id)
    except ChatAdminRequired:
        return "🚫 I need ban permissions to execute this action."
    except Exception as e:
        return f"🚫 Oops!\n{e}"

    return f"{mention(user_id, first_name)} was unbanned by {mention(admin_id, admin_name)}"


async def mute_user(user_id, first_name, admin_id, admin_name, chat_id, reason=None, time: datetime.timedelta | None = None):
    try:
        if time:
            # Pyrogram accepts datetime for until_date
            mute_end_time = datetime.datetime.now() + time
            await app.restrict_chat_member(chat_id, user_id, ChatPermissions(), mute_end_time)
        else:
            await app.restrict_chat_member(chat_id, user_id, ChatPermissions())
    except ChatAdminRequired:
        return "🔇 I need mute permissions to do that.", False
    except UserAdminInvalid:
        return "🛡️ I won't mute an admin!", False
    except Exception as e:
        bot_id = (await app.get_me()).id
        if user_id == bot_id:
            return "Why should I mute myself? No thanks.", False
        return f"🚫 Oops!\n{e}", False

    msg_text = f"{mention(user_id, first_name)} was muted by {mention(admin_id, admin_name)}\n"
    if reason:
        msg_text += f"Reason: `{reason}`\n"
    if time:
        msg_text += f"Time: `{time}`\n"
    return msg_text, True


async def unmute_user(user_id, first_name, admin_id, admin_name, chat_id):
    try:
        await app.restrict_chat_member(
            chat_id,
            user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_send_polls=True,
                can_add_web_page_previews=True,
                can_invite_users=True
            )
        )
    except ChatAdminRequired:
        return "🔇 I need unmute permissions to do that."
    except Exception as e:
        return f"🚫 Oops!\n{e}"

    return f"{mention(user_id, first_name)} was unmuted by {mention(admin_id, admin_name)}"


# ---------------------- Command Handlers ----------------------
@app.on_message(filters.command(["ban"]))
async def ban_command_handler(client, message):
    err = ensure_sender(message)
    if err:
        return await message.reply_text(err)

    chat = message.chat

    # Human admin privileges
    admin_id = message.from_user.id
    admin_name = message.from_user.first_name
    member = await chat.get_member(admin_id)
    err = ensure_admin_privileges(member, "ban")
    if err:
        return await message.reply_text(err)

    # Bot privileges
    err = await ensure_bot_privileges(chat, "ban")
    if err:
        return await message.reply_text(err)

    # Extract target
    target_id, target_name, reason = await extract_target(message)
    if not target_id:
        return

    # Validate target
    err = await ensure_target_valid(chat, target_id)
    if err:
        return await message.reply_text(err)

    msg_text, _ = await ban_user(target_id, target_name, admin_id, admin_name, chat.id, reason)
    await message.reply_text(msg_text)


@app.on_message(filters.command(["unban"]))
async def unban_command_handler(client, message):
    err = ensure_sender(message)
    if err:
        return await message.reply_text(err)

    chat = message.chat

    admin_id = message.from_user.id
    admin_name = message.from_user.first_name
    member = await chat.get_member(admin_id)
    err = ensure_admin_privileges(member, "unban")
    if err:
        return await message.reply_text(err)

    err = await ensure_bot_privileges(chat, "unban")
    if err:
        return await message.reply_text(err)

    target_id, target_name, _ = await extract_target(message, need_reason=False)
    if not target_id:
        return

    msg_text = await unban_user(target_id, target_name, admin_id, admin_name, chat.id)
    await message.reply_text(msg_text)


@app.on_message(filters.command(["mute"]))
async def mute_command_handler(client, message):
    err = ensure_sender(message)
    if err:
        return await message.reply_text(err)

    chat = message.chat

    admin_id = message.from_user.id
    admin_name = message.from_user.first_name
    member = await chat.get_member(admin_id)
    err = ensure_admin_privileges(member, "mute")
    if err:
        return await message.reply_text(err)

    err = await ensure_bot_privileges(chat, "mute")
    if err:
        return await message.reply_text(err)

    target_id, target_name, reason = await extract_target(message)
    if not target_id:
        return

    err = await ensure_target_valid(chat, target_id)
    if err:
        return await message.reply_text(err)

    msg_text, _ = await mute_user(target_id, target_name, admin_id, admin_name, chat.id, reason)
    await message.reply_text(msg_text)


@app.on_message(filters.command(["unmute"]))
async def unmute_command_handler(client, message):
    err = ensure_sender(message)
    if err:
        return await message.reply_text(err)

    chat = message.chat

    admin_id = message.from_user.id
    admin_name = message.from_user.first_name
    member = await chat.get_member(admin_id)
    err = ensure_admin_privileges(member, "unmute")
    if err:
        return await message.reply_text(err)

    err = await ensure_bot_privileges(chat, "unmute")
    if err:
        return await message.reply_text(err)

    target_id, target_name, _ = await extract_target(message, need_reason=False)
    if not target_id:
        return

    # Unmute also shouldn't try on admins/owner/bot; check is harmless
    err = await ensure_target_valid(chat, target_id)
    if err:
        return await message.reply_text(err)

    msg_text = await unmute_user(target_id, target_name, admin_id, admin_name, chat.id)
    await message.reply_text(msg_text)


@app.on_message(filters.command(["tmute"]))
async def tmute_command_handler(client, message):
    err = ensure_sender(message)
    if err:
        return await message.reply_text(err)

    chat = message.chat

    admin_id = message.from_user.id
    admin_name = message.from_user.first_name
    member = await chat.get_member(admin_id)
    err = ensure_admin_privileges(member, "mute")
    if err:
        return await message.reply_text(err)

    err = await ensure_bot_privileges(chat, "mute")
    if err:
        return await message.reply_text(err)

    target_id, target_name, mute_duration = await extract_tmute_target(message)
    if not target_id:
        return

    err = await ensure_target_valid(chat, target_id)
    if err:
        return await message.reply_text(err)

    msg_text, _ = await mute_user(target_id, target_name, admin_id, admin_name, chat.id, None, mute_duration)
    await message.reply_text(msg_text)


# ---------------------- Helpers ----------------------
async def extract_target(message, need_reason=True):
    """Extract target user and optional reason."""
    target_id = None
    target_name = None
    reason = None

    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
        if need_reason and len(message.command) > 1:
            reason = message.text.split(None, 1)[1]
    elif len(message.command) > 1:
        arg = message.command[1]
        try:
            target_id = int(arg)
            target_name = "User"
        except ValueError:
            user_obj = await get_userid_from_username(arg)
            if not user_obj:
                await message.reply_text("❗ I couldn’t find that user. Make sure the username is correct.")
                return None, None, None
            target_id, target_name = user_obj
        if need_reason:
            # everything after the first arg
            reason = message.text.partition(arg)[2].strip() or None
    else:
        await message.reply_text("📌 Please specify a valid user or reply to their message.")
        return None, None, None

    return target_id, target_name, reason


async def extract_tmute_target(message):
    """Extract target user and mute duration for timed mute. Format: /tmute <reply|user> <2m|3h|1d>"""
    # Case 1: reply + time after command
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
        if len(message.command) < 2:
            await message.reply_text("⚠️ Invalid format!\nFormat: `/tmute <time>`")
            return None, None, None
        time_str = message.command[1]
    # Case 2: /tmute <user> <time>
    elif len(message.command) > 2:
        arg = message.command[1]
        try:
            target_id = int(arg)
            target_name = "User"
        except ValueError:
            user_obj = await get_userid_from_username(arg)
            if not user_obj:
                await message.reply_text("❗ I couldn’t find that user. Make sure the username is correct.")
                return None, None, None
            target_id, target_name = user_obj
        time_str = message.command[2]
    else:
        await message.reply_text("📌 Please specify a valid user and time.\nFormat: `/tmute @user 2m`")
        return None, None, None

    # Parse time like 2m / 3h / 1d
    if not time_str or time_str[-1] not in ("m", "h", "d"):
        await message.reply_text("⚠️ Invalid time format!\nUse m/h/d suffix, e.g., `2m`, `3h`, `1d`.")
        return None, None, None
    try:
        amount = int(time_str[:-1])
    except ValueError:
        await message.reply_text("⚠️ Invalid number in time format.")
        return None, None, None

    duration_map = {
        "m": datetime.timedelta(minutes=amount),
        "h": datetime.timedelta(hours=amount),
        "d": datetime.timedelta(days=amount),
    }
    return target_id, target_name, duration_map[time_str[-1]]
