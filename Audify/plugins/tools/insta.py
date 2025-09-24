import os
import re
import yt_dlp
from random import randint
from mimetypes import guess_type
from pyrogram import filters
from pyrogram.types import Message

from Audify import app
from config import LOGGER_ID

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def is_video(file_path):
    mime = guess_type(file_path)[0]
    return mime and mime.startswith("video")

def is_image(file_path):
    mime = guess_type(file_path)[0]
    return mime and mime.startswith("image")

# Match any instagram.com or instagr.am link
IG_REGEX = r"(https?://(?:www\.)?(?:instagram\.com|instagr\.am)[^\s]+)"

@app.on_message(filters.text & filters.regex(IG_REGEX))
async def download_instagram_media(client, message: Message):
    match = re.search(IG_REGEX, message.text)
    if not match:
        return

    url = match.group(1).strip()
    await app.send_message(LOGGER_ID, f"📌 Caught IG URL: {url}")

    status_msg = await message.reply_text("📥 Downloading media from Instagram...")

    try:
        ydl_opts = {
            "outtmpl": f"{DOWNLOAD_DIR}/%(title).70s_{randint(1000,9999)}.%(ext)s",
            "format": "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "retries": 5
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            results = info["entries"] if "entries" in info else [info]

            for entry in results:
                file_path = ydl.prepare_filename(entry)
                if not os.path.exists(file_path):
                    continue

                await status_msg.delete()

                if is_video(file_path):
                    await message.reply_video(
                        video=file_path,
                        caption="📹 Instagram Video",
                        supports_streaming=True
                    )
                elif is_image(file_path):
                    await message.reply_photo(
                        photo=file_path,
                        caption="🖼️ Instagram Photo"
                    )
                else:
                    await message.reply_document(
                        document=file_path,
                        caption="📎 Media File"
                    )

                os.remove(file_path)

    except Exception as e:
        error_msg = f"❌ Error while downloading:\n`{e}`"
        try:
            await status_msg.edit(error_msg)
        except:
            await message.reply_text(error_msg)
        await app.send_message(LOGGER_ID, error_msg)
