# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Audify™. All rights reserved.
# ---------------------------------------------------------

import time
import logging
import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import (
    FloodWait,
    RPCError,
    Forbidden,
    UserIsBlocked,
    ChatWriteForbidden,
    PeerIdInvalid,
)
from pyrogram.types import Message

from Audify import app
from Audify.misc import SUDOERS
from Audify.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from Audify.utils.decorators.language import language
from Audify.utils.formatters import alpha_to_int
from config import adminlist

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("Broadcast")

# Global broadcast status
BROADCAST_STATUS = {
    "active": False,
    "sent": 0,
    "failed": 0,
    "total": 0,
    "start_time": 0,
    "users": 0,
    "chats": 0,
    "mode": "",
    "sent_users": 0,
    "sent_chats": 0,
}


@app.on_message(filters.command("broadcast") & SUDOERS)
async def broadcast_command(client, message: Message):
    global BROADCAST_STATUS

    command = message.text.lower()
    mode = "forward" if "-forward" in command else "copy"

    # Determine recipients
    if "-all" in command:
        users = await get_served_users()
        chats = await get_served_chats()
        target_users = [u["user_id"] for u in users]
        target_chats = [c["chat_id"] for c in chats]
    elif "-users" in command:
        users = await get_served_users()
        target_users = [u["user_id"] for u in users]
        target_chats = []
    elif "-chats" in command:
        chats = await get_served_chats()
        target_chats = [c["chat_id"] for c in chats]
        target_users = []
    else:
        return await message.reply_text("❗ Usage:\n/broadcast -all/-users/-chats [-forward]")

    if not target_users and not target_chats:
        return await message.reply_text("⚠ No recipients found.")

    # Get content
    if message.reply_to_message:
        content = message.reply_to_message
    else:
        text = message.text
        for kw in ["/broadcast", "-forward", "-all", "-users", "-chats"]:
            text = text.replace(kw, "")
        text = text.strip()
        if not text:
            return await message.reply_text("📝 Provide a message or reply to one.")
        content = text

    # Flatten targets and store local mutable lists so we can remove broken targets on the fly
    target_users = list(target_users)
    target_chats = list(target_chats)
    targets = target_users + target_chats
    total = len(targets) or 1  # avoid zero division later

    BROADCAST_STATUS.update({
        "active": True,
        "sent": 0,
        "failed": 0,
        "total": len(targets),
        "start_time": time.time(),
        "users": len(target_users),
        "chats": len(target_chats),
        "mode": mode,
    })

    logger.info(f"Broadcast started: mode={mode}, users={len(target_users)}, chats={len(target_chats)}")
    status_msg = await message.reply_text("📡 Broadcasting started...")

    async def deliver(chat_id):
        """Send or copy/forward content to chat_id with robust error handling."""
        try:
            if isinstance(content, str):
                await app.send_message(chat_id, content)
            elif mode == "forward":
                # forwarding the replied message
                await app.forward_messages(chat_id, message.chat.id, [content.id])
            else:
                await content.copy(chat_id)

            BROADCAST_STATUS["sent"] += 1
            if chat_id in target_users:
                BROADCAST_STATUS["sent_users"] += 1
            else:
                BROADCAST_STATUS["sent_chats"] += 1

        except FloodWait as e:
            # wait the required time (but cap to prevent extremely long sleeps)
            wait = min(int(e.value), 120)
            logger.warning(f"FloodWait for {wait}s while sending to {chat_id}")
            await asyncio.sleep(wait)
            return await deliver(chat_id)

        except (Forbidden, UserIsBlocked, ChatWriteForbidden, PeerIdInvalid) as e:
            # These mean bot cannot message that target anymore — skip and remove locally
            BROADCAST_STATUS["failed"] += 1
            logger.warning(f"Broadcast - unreachable target {chat_id}: {e!r}")
            # remove from local lists so we don't retry this chat again in this run
            try:
                if chat_id in targets:
                    targets.remove(chat_id)
                if chat_id in target_users:
                    target_users.remove(chat_id)
                if chat_id in target_chats:
                    target_chats.remove(chat_id)
            except Exception:
                # ignore removal errors
                pass
            # NOTE: If you have DB removal functions (e.g., remove_served_user/chat),
            # call them here to keep DB clean.
            return

        except RPCError as e:
            # Generic Telegram API error — log and continue
            BROADCAST_STATUS["failed"] += 1
            logger.warning(f"Broadcast - RPCError on {chat_id}: {e!r}")
            return

        except Exception as e:
            BROADCAST_STATUS["failed"] += 1
            logger.exception(f"Error delivering to {chat_id}: {e}")
            return

    # Batching and concurrent delivery
    BATCH_SIZE = 100
    # compute fresh total from targets in case modifications happen
    for i in range(0, len(targets), BATCH_SIZE):
        batch = list(targets[i:i + BATCH_SIZE])
        tasks = [deliver(chat_id) for chat_id in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        # short pause to be polite to Telegram
        await asyncio.sleep(1.5)

        sent_plus_failed = BROADCAST_STATUS['sent'] + BROADCAST_STATUS['failed']
        denom = max(len(targets), 1)
        percent = round(sent_plus_failed / denom * 100, 2)
        try:
            await status_msg.edit_text(
                f"📣 <b>Broadcast In Progress</b>\n"
                f"✅ Sent: <code>{BROADCAST_STATUS['sent']}</code>\n"
                f"❌ Failed: <code>{BROADCAST_STATUS['failed']}</code>\n"
                f"📦 Total: <code>{BROADCAST_STATUS['total']}</code>\n"
                f"├ Users: <code>{BROADCAST_STATUS['users']}</code>\n                "
                f"└ Chats: <code>{BROADCAST_STATUS['chats']}</code>\n"
                f"🔃 Progress: <code>{percent}%</code>"
            )
        except Exception:
            # ignore mid-broadcast status edit errors
            pass

    BROADCAST_STATUS["active"] = False
    elapsed = round(time.time() - BROADCAST_STATUS["start_time"])
    logger.info(f"Broadcast complete: {BROADCAST_STATUS['sent']} sent, {BROADCAST_STATUS['failed']} failed")

    try:
        await status_msg.edit_text(
            f"✅ <b>Broadcast Complete!</b>\n\n"
            f"🔘 Mode: <code>{BROADCAST_STATUS['mode']}</code>\n"
            f"📦 Total Targets: <code>{BROADCAST_STATUS['total']}</code>\n"
            f"📬 Delivered: <code>{BROADCAST_STATUS['sent']}</code>\n"
            f"├ Users: <code>{BROADCAST_STATUS['sent_users']}</code>\n"
            f"└ Chats: <code>{BROADCAST_STATUS['sent_chats']}</code>\n"
            f"❌ Failed: <code>{BROADCAST_STATUS['failed']}</code>\n"
            f"⏰ Time Taken: <code>{elapsed}s</code>"
        )
    except Exception:
        # if final edit fails, send a new message instead
        await message.reply_text(
            f"✅ Broadcast finished. Sent: {BROADCAST_STATUS['sent']}, Failed: {BROADCAST_STATUS['failed']}"
        )


@app.on_message(filters.command("status") & SUDOERS)
async def broadcast_status(client, message: Message):
    if not BROADCAST_STATUS["active"]:
        return await message.reply_text("📡 No active broadcast.")

    elapsed = round(time.time() - BROADCAST_STATUS["start_time"])
    sent = BROADCAST_STATUS["sent"]
    failed = BROADCAST_STATUS["failed"]
    total = BROADCAST_STATUS["total"] or 1
    percent = round((sent + failed) / total * 100, 2)

    eta = (elapsed / max((sent + failed), 1)) * (total - (sent + failed))
    eta_fmt = f"{int(eta // 60)}m {int(eta % 60)}s"

    bar = f"[{'█' * int(percent // 5)}{'░' * (20 - int(percent // 5))}]"

    await message.reply_text(
        f"📊 <b>Live Broadcast Status</b>\n\n"
        f"{bar} <code>{percent}%</code>\n"
        f"✅ Sent: <code>{sent}</code>\n"
        f"❌ Failed: <code>{failed}</code>\n"
        f"📦 Total: <code>{total}</code>\n"
        f"⏱ ETA: <code>{eta_fmt}</code>\n"
        f"🕒 Elapsed: <code>{elapsed}s</code>"
    )


async def auto_clean():
    """Periodically populate adminlist for active chats safely."""
    while True:
        await asyncio.sleep(10)
        try:
            served_chats = await get_active_chats()
            for chat_id in served_chats:
                try:
                    if chat_id not in adminlist:
                        adminlist[chat_id] = []
                    else:
                        # refresh list each run
                        adminlist[chat_id].clear()

                    # iterate administrators safely
                    async for member in app.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
                        # include creator OR admins with manage video chats privilege
                        try:
                            is_creator = (getattr(member, "status", None) == "creator")
                            can_manage_vc = getattr(member.privileges, "can_manage_video_chats", False)
                            if is_creator or can_manage_vc:
                                if member.user and getattr(member.user, "id", None):
                                    adminlist[chat_id].append(member.user.id)
                        except Exception:
                            # skip problematic member objects
                            continue

                    # add additional authorized users (from your authuser DB)
                    authusers = await get_authuser_names(chat_id) or []
                    for user in authusers:
                        try:
                            user_id = await alpha_to_int(user)
                            if user_id not in adminlist[chat_id]:
                                adminlist[chat_id].append(user_id)
                        except Exception:
                            continue

                except (RPCError, Forbidden, PeerIdInvalid) as e:
                    # can't access this chat — skip it and continue with others
                    logger.warning(f"AutoClean - cannot fetch admins for {chat_id}: {e!r}")
                    # optional: remove chat_id from adminlist/db here if desired
                    continue

        except Exception as e:
            logger.warning(f"AutoClean error: {e!r}")


# Start auto clean task
try:
    asyncio.create_task(auto_clean())
except RuntimeError:
    # In some startup scenarios event loop may not be running; schedule later if needed.
    logger.info("Event loop not ready — auto_clean will start with app.run." )
