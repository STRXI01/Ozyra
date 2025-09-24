import os
import shutil
import requests
import yt_dlp
import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Audify import app
from config import BOT_LOGS_CHANNEL
from typing import Union
from youtubesearchpython.__future__ import VideosSearch
import aiohttp


def duration_to_seconds(duration_str: str) -> int:
    parts = duration_str.split(":")
    seconds = 0
    for i in range(len(parts)):
        seconds += int(parts[-(i + 1)]) * (60 ** i)
    return seconds


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL or return the string if it's already an ID"""
    import re
    
    # YouTube URL patterns
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume it's already a video ID or search query
    return url


async def get_cookies_from_api():
    """Fetch cookies.txt content from the API and save it locally"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://v0-mongo-db-api-setup.vercel.app/api/cookies.txt") as response:
                if response.status == 200:
                    cookies_content = await response.text()
                    
                    # Create cookies directory if it doesn't exist
                    cookie_dir = f"{os.getcwd()}/cookies"
                    os.makedirs(cookie_dir, exist_ok=True)
                    
                    # Save cookies to a temporary file
                    cookie_file_path = os.path.join(cookie_dir, "api_cookies.txt")
                    with open(cookie_file_path, 'w') as f:
                        f.write(cookies_content)
                    
                    return cookie_file_path
                else:
                    print(f"Failed to fetch cookies from API: {response.status}")
                    return None
    except Exception as e:
        print(f"Error fetching cookies from API: {e}")
        return None


def get_cookies_file() -> str:
    """Get cookies file path or create one from browser"""
    cookies_path = "cookies.txt"
    
    # Check if cookies file already exists
    if os.path.exists(cookies_path):
        return cookies_path
    
    # Try to extract cookies from browser (you can customize this)
    try:
        # Try Chrome first, then Firefox
        browsers = ["chrome", "firefox", "edge", "safari"]
        for browser in browsers:
            try:
                # This would extract cookies from browser to file
                import subprocess
                result = subprocess.run([
                    "yt-dlp", 
                    "--cookies", cookies_path, 
                    "--cookies-from-browser", browser,
                    "--no-download",
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # dummy video
                ], capture_output=True, text=True, timeout=30)
                
                if os.path.exists(cookies_path):
                    print(f"Successfully extracted cookies from {browser}")
                    return cookies_path
            except:
                continue
    except Exception as e:
        print(f"Could not extract cookies from browser: {e}")
    
    return None


class ProgressHook:
    def __init__(self, status_message):
        self.status_message = status_message
        self.last_update = 0
        
    def __call__(self, d):
        if d['status'] == 'downloading':
            # Update progress every 5 seconds to avoid rate limiting
            import time
            current_time = time.time()
            if current_time - self.last_update > 5:
                try:
                    if 'total_bytes' in d:
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d['total_bytes']
                        percentage = (downloaded / total) * 100
                        speed = d.get('speed', 0)
                        if speed:
                            speed_mb = speed / (1024 * 1024)
                            eta = d.get('eta', 0)
                            eta_str = f"{eta}s" if eta else "Unknown"
                            asyncio.create_task(self.status_message.edit(
                                f"⬇️ Downloading: {percentage:.1f}%\n"
                                f"📊 Speed: {speed_mb:.2f} MB/s\n"
                                f"⏰ ETA: {eta_str}"
                            ))
                        else:
                            asyncio.create_task(self.status_message.edit(
                                f"⬇️ Downloading: {percentage:.1f}%"
                            ))
                    else:
                        asyncio.create_task(self.status_message.edit("⬇️ Downloading..."))
                    self.last_update = current_time
                except:
                    pass
        elif d['status'] == 'finished':
            asyncio.create_task(self.status_message.edit("🎵 Processing audio..."))


async def download_audio_ytdlp(video_id: str, download_path: str, status_message) -> tuple[bool, dict]:
    """Download audio using yt-dlp with progress tracking and cookies support"""
    try:
        # Get cookies from API first
        cookies_file = await get_cookies_from_api()
        if not cookies_file:
            # Fallback to local cookies
            cookies_file = get_cookies_file()
        
        # Create progress hook
        progress_hook = ProgressHook(status_message)
        
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": download_path,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        # Add cookies if available
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts["cookiefile"] = cookies_file
            print(f"Using cookies from: {cookies_file}")
        
        await status_message.edit("📋 Getting video info...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
            await status_message.edit("⬇️ Starting download...")
            
            # Then download with progress tracking
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            
            # Wait for file to be completely processed
            max_wait = 60  # Maximum 60 seconds wait
            wait_count = 0
            expected_file = download_path.replace('.%(ext)s', '.mp3')
            
            await status_message.edit("⏳ Finalizing download...")
            
            while wait_count < max_wait:
                if os.path.exists(expected_file) and os.path.getsize(expected_file) > 0:
                    # Check if file is still being written
                    initial_size = os.path.getsize(expected_file)
                    await asyncio.sleep(2)
                    final_size = os.path.getsize(expected_file)
                    
                    if initial_size == final_size:
                        # File is complete
                        break
                
                await asyncio.sleep(1)
                wait_count += 1
            
            # Verify file exists and has content
            final_path = expected_file if os.path.exists(expected_file) else download_path
            if os.path.exists(final_path) and os.path.getsize(final_path) > 0:
                await status_message.edit("✅ Download complete!")
                return True, info
            else:
                raise Exception("Downloaded file not found or empty")
            
    except Exception as e:
        print(f"yt-dlp download failed: {e}")
        await status_message.edit(f"❌ Download failed: {str(e)}")
        return False, {}


async def wait_for_complete_download(file_path: str, timeout: int = 120) -> bool:
    """Wait for file to be completely downloaded and stable"""
    start_time = asyncio.get_event_loop().time()
    last_size = 0
    stable_count = 0
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        if os.path.exists(file_path):
            current_size = os.path.getsize(file_path)
            
            if current_size > 0:
                if current_size == last_size:
                    stable_count += 1
                    # File size hasn't changed for 3 consecutive checks (6 seconds)
                    if stable_count >= 3:
                        return True
                else:
                    stable_count = 0
                    last_size = current_size
                    
        await asyncio.sleep(2)
    
    return False


@app.on_message(filters.command(["song", "music"]))
async def song_handler(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❗ Provide a song name or YouTube link.")
    
    query = " ".join(message.command[1:])
    status = await message.reply_text("🔍 Searching for audio...")

    duration = 0
    title = None
    thumbnail_url = None
    info_dict = {}
    
    try:
        video_id = extract_video_id(query)
        # Check if it's a valid video ID (11 characters) or if it's a search query
        if len(video_id) == 11 and video_id.replace('-', '').replace('_', '').isalnum():
            link = f"https://youtu.be/{video_id}"
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        else:
            raise Exception("Not a valid video ID, search needed")
            
    except:
        try:
            await status.edit("🔍 Searching YouTube...")
            results = (await VideosSearch(query, limit=1).next())["result"]
            if not results:
                return await status.edit("❌ No results found.")
            video_id = results[0]["id"]
            link = results[0]["link"]
            title = results[0]["title"].strip().replace("/", "-").replace("\\", "-")
            thumbnail_url = results[0]["thumbnails"][0]["url"]
            duration_text = results[0].get("duration", None)
            if duration_text and ":" in duration_text:
                duration = duration_to_seconds(duration_text)
        except Exception as e:
            return await status.edit(f"❌ YouTube search failed.\nError: `{e}`")

    # Sanitize title if we have one, otherwise we'll get it from yt-dlp
    if title:
        title = "".join(c if c.isalnum() or c in " ._-()" else "_" for c in title)

    new_filename = f"{title or video_id}.%(ext)s"
    download_path = os.path.join("downloads", new_filename)
    os.makedirs("downloads", exist_ok=True)

    try:
        # Download using yt-dlp with progress tracking
        success, info_dict = await download_audio_ytdlp(video_id, download_path, status)
        if not success:
            raise Exception("yt-dlp download failed")
        
        # Extract info from yt-dlp if we didn't get it from search
        if info_dict:
            if not title:
                title = info_dict.get("title", f"yt-audio-{video_id}")
                title = "".join(c if c.isalnum() or c in " ._-()" else "_" for c in title)
            if not duration:
                duration = int(info_dict.get("duration", 0))
            if not thumbnail_url:
                thumbnails = info_dict.get("thumbnails", [])
                if thumbnails:
                    thumbnail_url = thumbnails[-1].get("url")
            
        # Find the actual downloaded file
        expected_files = [
            os.path.join("downloads", f"{title}.mp3"),
            os.path.join("downloads", f"{video_id}.mp3"),
            download_path.replace('.%(ext)s', '.mp3')
        ]
        
        final_download_path = None
        for file_path in expected_files:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                final_download_path = file_path
                break
                
        if not final_download_path:
            raise Exception("Downloaded file not found")
            
        download_path = final_download_path
        
        # Wait for complete download with verification
        await status.edit("⏳ Verifying download completion...")
        if not await wait_for_complete_download(download_path):
            raise Exception("Download verification failed")
            
    except Exception as e:
        return await status.edit(f"❌ Download failed.\nError: `{e}`")

    # Final verification
    if not os.path.isfile(download_path) or os.path.getsize(download_path) == 0:
        return await status.edit("❌ Download failed - file not found or empty.")

    await status.edit("🖼️ Downloading thumbnail...")

    # Download thumbnail
    thumb_path = None
    if thumbnail_url:
        try:
            thumb_response = requests.get(thumbnail_url, stream=True, timeout=10)
            if thumb_response.status_code == 200:
                thumb_path = os.path.join("downloads", f"{video_id}_thumb.jpg")
                with open(thumb_path, "wb") as f:
                    for chunk in thumb_response.iter_content(1024):
                        f.write(chunk)
        except Exception as thumb_error:
            print(f"Thumbnail download failed: {thumb_error}")

    # Final caption and buttons
    caption = (
        f"🎶 <b>Track</b> : <b>{title or 'Unknown'}</b>\n\n"
        f"⏱️ <b>Duration</b> : {duration // 60} minutes {duration % 60:02d} seconds\n\n"
        f"🙋 <b>Requested by</b> : {message.from_user.mention}"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Watch on YouTube", url=link)]
    ])

    await status.edit("📤 Uploading audio file...")

    try:
        # Send to user (group or PM)
        await message.reply_audio(
            audio=download_path,
            caption=caption,
            thumb=thumb_path,
            title=title or "Unknown",
            performer="KawaiMusic",
            duration=duration,
            reply_markup=buttons
        )

        # Try logging to BOT_LOGS_CHANNEL
        try:
            await app.send_audio(
                chat_id=BOT_LOGS_CHANNEL,
                audio=download_path,
                caption=caption,
                thumb=thumb_path,
                title=title or "Unknown",
                performer="AlphaBotz",
                duration=duration,
                reply_markup=buttons
            )
        except Exception as log_err:
            print(f"[LOG ERROR] Could not send to BOT_LOGS_CHANNEL: {log_err}")

    except Exception as e:
        await status.edit(f"❌ Failed to send audio: `{e}`")
    else:
        await status.delete()

    # Cleanup
    try:
        if os.path.isfile(download_path):
            os.remove(download_path)
        if thumb_path and os.path.isfile(thumb_path):
            os.remove(thumb_path)
    except Exception as cleanup_error:
        print(f"Cleanup error: {cleanup_error}")
