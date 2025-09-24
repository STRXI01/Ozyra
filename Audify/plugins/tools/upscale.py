# upscale.py

# ---
# Audify Bot - All rights reserved
# ---
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---

import os
import aiohttp
import base64
from pyrogram import filters
from pyrogram.types import Message
from Audify import app

API_URL = "https://www.simpleimageresizer.com/upscale-image-action"

@app.on_message(filters.command(["upscale", "enhance"]) & filters.reply)
async def upscale_image(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("❌ Please reply to a photo with /upscale or /enhance.", quote=True)

    msg = await message.reply("🖼️ Upscaling the image 4x... Please wait ⏳")

    download_path = None

    try:
        # Download original photo
        photo = message.reply_to_message.photo
        download_path = await app.download_media(photo)

        # Read and encode image to base64
        with open(download_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        # Prepare payload for the new API
        payload = {
            "uploadedFilesDataKey": {
                "fileNamesArrayKey": [os.path.basename(download_path)],
                "strings64BaseArrayKey": [b64_image]
            },
            "upscaleValueKey": "4"  # Always 4x upscale
        }

        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.simpleimageresizer.com",
            "Referer": "https://www.simpleimageresizer.com/image-upscaler",
            "User-Agent": "Mozilla/5.0"
        }

        # Send request to new API
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    return await msg.edit(f"❌ Upscaling failed. API responded with status {response.status}.")
                
                result = await response.json()

        # Check if upscaling was successful
        if not result.get("success") or "downloadUrl" not in result:
            return await msg.edit("❌ Upscaling failed. No image returned.")

        # Download upscaled image
        upscale_url = result["downloadUrl"][0]
        upscale_path = f"upscaled_{message.chat.id}_{message.message_id}.png"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(upscale_url) as r:
                if r.status != 200:
                    return await msg.edit("❌ Failed to download upscaled image.")
                
                with open(upscale_path, "wb") as f:
                    f.write(await r.read())

        # Send the upscaled image
        await message.reply_photo(upscale_path, caption="✨ Image successfully enhanced 4x using AI Upscaler.")
        await msg.delete()

        # Clean up the upscaled image file
        if os.path.exists(upscale_path):
            try:
                os.remove(upscale_path)
            except Exception:
                pass

    except Exception as e:
        await msg.edit(f"❌ Error during upscaling:\n<code>{str(e)}</code>")

    finally:
        # Clean up the downloaded original image
        if download_path and os.path.exists(download_path):
            try:
                os.remove(download_path)
            except Exception:
                pass
