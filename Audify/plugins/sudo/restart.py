import asyncio
import os
import shutil
import socket
from datetime import datetime

import urllib3
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from pyrogram import filters

import config
from Audify import app
from Audify.misc import HAPP, SUDOERS, XCB
from Audify.utils.database import (
    get_active_chats,
    remove_active_chat,
    remove_active_video_chat,
)
from Audify.utils.decorators.language import language
from Audify.utils.pastebin import AudifyBin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


async def is_heroku():
    return "heroku" in socket.getfqdn()


@app.on_message(filters.command(["getlog", "logs", "getlogs"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"]) & SUDOERS)
@language
async def log_(client, message, _):
    try:
        await message.reply_document(document="log.txt")
    except:
        await message.reply_text(_["server_1"])


@app.on_message(filters.command(["update", "gitpull"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"]) & SUDOERS)
@language
async def update_(client, message, _):
    # Initial response with a modern loading message
    loader = ["⠋ ᴄʜᴇᴄᴋɪɴɢ ᴜᴘᴅᴀᴛᴇꜱ", "⠙ ᴄʜᴇᴄᴋɪɴɢ ᴜᴘᴅᴀᴛᴇꜱ.", "⠹ ᴄʜᴇᴄᴋɪɴɢ ᴜᴘᴅᴀᴛᴇꜱ..", "⠸ ᴄʜᴇᴄᴋɪɴɢ ᴜᴘᴅᴀᴛᴇꜱ..."]
    response = await message.reply_text(loader[0])
    
    # Simulate loading animation
    for i in range(1, 4):
        await asyncio.sleep(1)
        await response.edit(loader[i])
    
    # Check if running on Heroku
    if await is_heroku():
        if HAPP is None:
            await response.edit("🚫 **ᴜᴘᴅᴀᴛᴇ ꜰᴀɪʟᴇᴅ**: ʜᴇʀᴏᴋᴜ ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ ɴᴏᴛ ᴄᴏɴꜰɪɢᴜʀᴇᴅ ᴘʀᴏᴘᴇʀʟʏ.")
            return
    
    try:
        repo = Repo()
    except GitCommandError:
        await response.edit("⚠️ **ᴇʀʀᴏʀ**: ɢɪᴛ ᴄᴏᴍᴍᴀɴᴅ ꜰᴀɪʟᴇᴅ. ᴘʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ꜱᴇᴛᴜᴘ.")
        return
    except InvalidGitRepositoryError:
        await response.edit("⚠️ **ᴇʀʀᴏʀ**: ɴᴏᴛ ᴀ ᴠᴀʟɪᴅ ɢɪᴛ ʀᴇᴘᴏꜱɪᴛᴏʀʏ.")
        return
    
    # Fetch updates from the remote repository
    to_exc = f"git fetch origin {config.UPSTREAM_BRANCH} &> /dev/null"
    os.system(to_exc)
    await asyncio.sleep(7)
    
    # Check for new commits
    verification = ""
    REPO_ = repo.remotes.origin.url.split(".git")[0]
    for checks in repo.iter_commits(f"HEAD..origin/{config.UPSTREAM_BRANCH}"):
        verification = str(checks.count())
    
    if verification == "":
        await response.edit("✅ **ɴᴏ ᴜᴘᴅᴀᴛᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ**: ʏᴏᴜʀ ʙᴏᴛ ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴜᴘ ᴛᴏ ᴅᴀᴛᴇ!")
        return
    
    # Format update details
    updates = ""
    ordinal = lambda format: "%d%s" % (
        format,
        "tsnrhtdd"[(format // 10 % 10 != 1) * (format % 10 < 4) * format % 10 :: 4],
    )
    for info in repo.iter_commits(f"HEAD..origin/{config.UPSTREAM_BRANCH}"):
        updates += (
            f"**#{info.count()}**: [{info.summary}]({REPO_}/ᴄᴏᴍᴍɪᴛ/{info})\n"
            f"  ⤷ ᴄᴏᴍᴍɪᴛᴛᴇᴅ ᴏɴ: {ordinal(int(datetime.fromtimestamp(info.committed_date).strftime('%d')))} "
            f"{datetime.fromtimestamp(info.committed_date).strftime('%b')}, "
            f"{datetime.fromtimestamp(info.committed_date).strftime('%Y')}\n\n"
        )
    
    # Modern update message
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    version = getattr(config, "VERSION", "Unknown")  # Replace with actual version if available
    _update_response_ = (
        "**ʙᴏᴛ ᴜᴘᴅᴀᴛᴇ ᴀᴠᴀɪʟᴀʙʟᴇ**\n\n"
        f"**ᴠᴇʀꜱɪᴏɴ**: {version}\n"
        f"**ᴜᴘᴅᴀᴛᴇ ᴛɪᴍᴇ**: {current_time}\n"
        "🔄 **ᴘᴜꜱʜɪɴɢ ᴜᴘᴅᴀᴛᴇꜱ ɴᴏᴡ...**\n\n"
        "**🔔 ᴄʜᴀɴɢᴇʟᴏɢ**:\n\n"
    )
    _final_updates_ = _update_response_ + updates
    
    # Handle message length for Telegram (4096 character limit)
    if len(_final_updates_) > 4096:
        url = await AudifyBin(updates)
        nrs = await response.edit(
            f"**ʙᴏᴛ ᴜᴘᴅᴀᴛᴇ ᴀᴠᴀɪʟᴀʙʟᴇ**\n\n"
            f"**ᴠᴇʀꜱɪᴏɴ**: {version}\n"
            f"**ᴜᴘᴅᴀᴛᴇ ᴛɪᴍᴇ**: {current_time}\n"
            "🔄 **ᴘᴜꜱʜɪɴɢ ᴜᴘᴅᴀᴛᴇꜱ ɴᴏᴡ...**\n\n"
            f"**🔔 ᴄʜᴀɴɢᴇʟᴏɢ**: [ᴠɪᴇᴡ ᴜᴘᴅᴀᴛᴇꜱ]({url})",
            disable_web_page_preview=True
        )
    else:
        nrs = await response.edit(_final_updates_, disable_web_page_preview=True)
    
    # Perform the git pull
    os.system("git stash &> /dev/null && git pull")
    
    # Notify active chats
    try:
        served_chats = await get_active_chats()
        for x in served_chats:
            try:
                await app.send_message(
                    chat_id=int(x),
                    text=f"🤖 {app.mention} ʜᴀꜱ ʙᴇᴇɴ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ ᴠᴇʀꜱɪᴏɴ {version}! ʀᴇꜱᴛᴀʀᴛɪɴɢ ɴᴏᴡ...",
                )
                await remove_active_chat(x)
                await remove_active_video_chat(x)
            except:
                pass
        await response.edit(f"{nrs.text}\n\n✅ **ᴜᴘᴅᴀᴛᴇ ᴄᴏᴍᴘʟᴇᴛᴇ**: ʙᴏᴛ ɪꜱ ʀᴇꜱᴛᴀʀᴛɪɴɢ...")
    except:
        pass
    
    # Handle Heroku or local restart
    if await is_heroku():
        try:
            os.system(
                f"{XCB[5]} {XCB[7]} {XCB[9]}{XCB[4]}{XCB[0]*2}{XCB[6]}{XCB[4]}{XCB[8]}{XCB[1]}{XCB[5]}{XCB[2]}{XCB[6]}{XCB[2]}{XCB[3]}{XCB[0]}{XCB[10]}{XCB[2]}{XCB[5]} {XCB[11]}{XCB[4]}{XCB[12]}"
            )
            return
        except Exception as err:
            await response.edit(f"{nrs.text}\n\n🚫 **ᴜᴘᴅᴀᴛᴇ ꜰᴀɪʟᴇᴅ**: ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴅᴜʀɪɴɢ ʀᴇꜱᴛᴀʀᴛ.")
            await app.send_message(
                chat_id=config.LOGGER_ID,
                text=f"⚠️ **ᴜᴘᴅᴀᴛᴇ ᴇʀʀᴏʀ**: {err}",
            )
            return
    else:
        os.system("pip3 install -r requirements.txt")
        os.system(f"kill -9 {os.getpid()} && bash start")
        exit()


@app.on_message(filters.command(["restart"]) & SUDOERS)
async def restart_(_, message):
    response = await message.reply_text("ʀᴇsᴛᴀʀᴛɪɴɢ...")
    ac_chats = await get_active_chats()
    for x in ac_chats:
        try:
            await app.send_message(
                chat_id=int(x),
                text=f"{app.mention} ɪs ʀᴇsᴛᴀʀᴛɪɴɢ...\n\nʏᴏᴜ ᴄᴀɴ sᴛᴀʀᴛ ᴩʟᴀʏɪɴɢ ᴀɢᴀɪɴ ᴀғᴛᴇʀ 15-20 sᴇᴄᴏɴᴅs.",
            )
            await remove_active_chat(x)
            await remove_active_video_chat(x)
        except:
            pass

    try:
        shutil.rmtree("downloads")
        shutil.rmtree("raw_files")
        shutil.rmtree("cache")
    except:
        pass
    await response.edit_text(
        "» ʀᴇsᴛᴀʀᴛ ᴘʀᴏᴄᴇss sᴛᴀʀᴛᴇᴅ, ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ғᴏʀ ғᴇᴡ sᴇᴄᴏɴᴅs ᴜɴᴛɪʟ ᴛʜᴇ ʙᴏᴛ sᴛᴀʀᴛs..."
    )
    os.system(f"kill -9 {os.getpid()} && bash start")
