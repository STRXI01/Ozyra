import time
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ChatType
from pyrogram.errors import ChatWriteForbidden, ChatAdminRequired, UserBannedInChannel
from youtubesearchpython.__future__ import VideosSearch

import config
from Audify import app
from Audify.misc import _boot_
from Audify.plugins.sudo.sudoers import sudoers_list
from Audify.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from Audify.utils.decorators.language import LanguageStart
from Audify.utils.formatters import get_readable_time
from Audify.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string


async def safe_send_with_effect(chat_id, text, **kwargs):
    """Safely send message with effect, fallback to normal message if effect fails"""
    try:
        # Try sending with message effect first
        return await app.send_message(chat_id=chat_id, text=text, message_effect_id=5104841245755180586, **kwargs)
    except Exception:
        # Fallback to normal message without effect
        return await app.send_message(chat_id=chat_id, text=text, **kwargs)


async def safe_reply_with_effect(message, text, **kwargs):
    """Safely reply with effect, fallback to normal reply if effect fails"""
    try:
        # Try replying with message effect first
        return await message.reply_text(text=text, message_effect_id=5104841245755180586, **kwargs)
    except Exception:
        # Fallback to normal reply without effect
        return await message.reply_text(text=text, **kwargs)


async def safe_reply_photo_with_effect(message, photo, caption, **kwargs):
    """Safely reply photo with effect, fallback to normal photo if effect fails"""
    try:
        # Try replying photo with message effect first
        return await message.reply_photo(photo=photo, caption=caption, message_effect_id=5104841245755180586, **kwargs)
    except Exception:
        # Fallback to normal photo without effect
        return await message.reply_photo(photo=photo, caption=caption, **kwargs)


async def safe_send_photo_with_effect(chat_id, photo, caption, **kwargs):
    """Safely send photo with effect, fallback to normal photo if effect fails"""
    try:
        # Try sending photo with message effect first
        return await app.send_photo(chat_id=chat_id, photo=photo, caption=caption, message_effect_id=5104841245755180586, **kwargs)
    except Exception:
        # Fallback to normal photo without effect
        return await app.send_photo(chat_id=chat_id, photo=photo, caption=caption, **kwargs)


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)

    # 🍓 React with animated emoji
    try:
        await message.react("🍓")
    except Exception:
        pass  # Ignore reaction errors

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel(_)
            return await safe_reply_photo_with_effect(
                message,
                photo=config.START_IMG_URL,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard
            )
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await safe_send_with_effect(
                    chat_id=config.LOGGER_ID,
                    text=f"<b>🛠️ Bot lookup</b>\n\n{message.from_user.mention} Just launched the bot to check the <b>Sudo List</b>.\n\n<b>👤 User ID :</b> <code>{message.from_user.id}</code>\n<b>🔗 Username :</b> @{message.from_user.username}"
                )
            return
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]
            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )
            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["S_B_8"], url=link),
                        InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                    ],
                ]
            )
            await m.delete()
            await safe_send_photo_with_effect(
                chat_id=message.chat.id,
                photo=config.START_IMG_URL,
                caption=searched_text,
                reply_markup=key
            )
            if await is_on_off(2):
                return await safe_send_with_effect(
                    chat_id=config.LOGGER_ID,
                    text=f"<b>🛠️ Bot started by</b>\n\n{message.from_user.mention} to fetch <b>Track Information</b>.\n\n<b>🆔 User ID :</b> <code>{message.from_user.id}</code>\n<b>🔗 Username :</b> @{message.from_user.username}"
                )
    else:
        out = private_panel(_)
        await safe_reply_photo_with_effect(
            message,
            photo=config.START_IMG_URL,
            caption=_["start_2"].format(message.from_user.mention, app.mention),
            reply_markup=InlineKeyboardMarkup(out)
        )
        if await is_on_off(2):
            return await safe_send_with_effect(
                chat_id=config.LOGGER_ID,
                text=f"<b>🛠️ #New User</b>\n\n{message.from_user.mention} 🤖 Started the Bot\n\n<b>🆔 User ID :</b> <code>{message.from_user.id}</code>\n<b>🔗 Username :</b> @{message.from_user.username}"
            )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    try:
        # Groups don't support message effects at all
        await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
            reply_markup=InlineKeyboardMarkup(out)
        )
        await add_served_chat(message.chat.id)
    except (ChatWriteForbidden, ChatAdminRequired, UserBannedInChannel):
        print(f"[WARN] Cannot send /start response in chat {message.chat.id} — no write permissions.")
    except Exception as e:
        print(f"[ERROR] start_gp failed in chat {message.chat.id}: {e}")


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except Exception as e:
                    print(f"[WARN] Could not ban user {member.id} in chat {message.chat.id}: {e}")
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    try:
                        # Groups don't support message effects
                        await message.reply_text(_["start_4"])
                    except ChatWriteForbidden:
                        print(f"[WARN] Cannot send join message in chat {message.chat.id}.")
                    return await app.leave_chat(message.chat.id)
                if message.chat.id in await blacklisted_chats():
                    try:
                        # Groups don't support message effects
                        await message.reply_text(
                            _["start_5"].format(
                                app.mention,
                                f"https://t.me/{app.username}?start=sudolist",
                                config.SUPPORT_CHAT,
                            ),
                            disable_web_page_preview=True
                        )
                    except ChatWriteForbidden:
                        print(f"[WARN] Cannot send blacklist message in chat {message.chat.id}.")
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                try:
                    # Groups don't support message effects
                    await message.reply_photo(
                        photo=config.START_IMG_URL,
                        caption=_["start_3"].format(
                            message.from_user.first_name,
                            app.mention,
                            message.chat.title,
                            app.mention,
                        ),
                        reply_markup=InlineKeyboardMarkup(out)
                    )
                except ChatWriteForbidden:
                    print(f"[WARN] Cannot send welcome panel in chat {message.chat.id}.")
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except Exception as ex:
            print(f" welcome() failed in chat skipping might be restricted {message.chat.id}: {ex}")
