# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---------------------------------------------------------

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.errors import ChatAdminRequired, RPCError
from Audify.utils.admin_check import admin_check

USE_AS_BOT = True

def f_sudo_filter(_, client, message):
    return bool(
        (
            (message.from_user and message.from_user.id in SUDO_USERS)
            or (message.sender_chat and message.sender_chat.id in SUDO_USERS)
        )
        and not message.edit_date
    )

sudo_filter = filters.create(func=f_sudo_filter, name="SudoFilter")


def onw_filter(_, client, message):
    if USE_AS_BOT:
        return bool(
            True
            and not message.edit_date
        )
    else:
        return bool(
            message.from_user
            and message.from_user.is_self
            and not message.edit_date
        )

f_onw_fliter = filters.create(func=onw_filter, name="OnwFilter")


async def admin_filter_f(_, client, message):
    # Skip edited messages
    if message.edit_date:
        return False

    # Skip non-group chats
    if message.chat.type not in (ChatType.SUPERGROUP, ChatType.GROUP):
        return False

    # Check if bot is admin first
    try:
        bot_member = await client.get_chat_member(message.chat.id, client.me.id)
        if bot_member.status not in ("administrator", "creator"):
            return False
    except ChatAdminRequired:
        return False
    except RPCError:
        return False

    # Now check if user is admin
    try:
        return await admin_check(message)
    except ChatAdminRequired:
        return False
    except RPCError:
        return False

admin_filter = filters.create(func=admin_filter_f, name="AdminFilter")
