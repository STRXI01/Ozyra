import asyncio
import os
import random
import re
import aiohttp
from pathlib import Path
from typing import Optional, Union, List, Tuple

import yt_dlp
from pyrogram import errors
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

from Audify.logging import LOGGER
from Audify.utils.database import is_on_off
from Audify.utils.formatters import time_to_seconds


class YouTubeUtils:
    cookie_index = 0

    @staticmethod
    def get_cookie_file() -> Optional[str]:
        cookie_dir = "Audify/assets"
        try:
            if not os.path.exists(cookie_dir):
                LOGGER(__name__).warning("Cookie directory '%s' does not exist.", cookie_dir)
                return None

            files = os.listdir(cookie_dir)
            cookies_files = [f for f in files if f.endswith(".txt") and f != "cookie_time.txt"]

            if not cookies_files:
                LOGGER(__name__).warning("No cookie files found in '%s'.", cookie_dir)
                return None

            selected_file = cookies_files[YouTubeUtils.cookie_index % len(cookies_files)]
            YouTubeUtils.cookie_index += 1
            return os.path.join(cookie_dir, selected_file)

        except Exception as e:
            LOGGER(__name__).warning("Error accessing cookie directory: %s", e)
            return None


class AlphaAPI:
    def __init__(self):
        self.base_url = "https://alphaapis.org/search"
    
    async def search_and_get_stream_url(self, query: str) -> Optional[dict]:
        try:
            async with aiohttp.ClientSession() as session:
                params = {"q": query}
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success") and data.get("results"):
                            first_result = data["results"][0]
                            stream_url = None
                            for download in first_result.get("download", []):
                                if download["quality"] == "320kbps":
                                    stream_url = download["url"]
                                    break
                            if not stream_url and first_result.get("download"):
                                stream_url = first_result["download"][-1]["url"]
                            
                            return {
                                "title": first_result.get("title", "Unknown"),
                                "artist": first_result.get("artist", "Unknown"),
                                "duration": int(first_result.get("duration", 0)),
                                "thumbnail": first_result.get("thumbnail", ""),
                                "stream_url": stream_url,
                                "year": first_result.get("year", "Unknown")
                            }
                    return None
        except Exception as e:
            LOGGER(__name__).error(f"AlphaAPI error: {e}")
            return None


async def shell_cmd(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        error_str = errorz.decode("utf-8").lower()
        if "unavailable videos are hidden" in error_str:
            return out.decode("utf-8")
        return error_str
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be|music\.youtube\.com)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.alpha_api = AlphaAPI()

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", YouTubeUtils.get_cookie_file(),
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        if "music.youtube.com" in link:
            link = link.replace("music.youtube.com", "www.youtube.com")
        playlist = await shell_cmd(
            f"yt-dlp --cookies {YouTubeUtils.get_cookie_file()} -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        
        alpha_result = await self.alpha_api.search_and_get_stream_url(title)
        if alpha_result and alpha_result.get("stream_url"):
            track_details = {
                "title": alpha_result["title"],
                "link": alpha_result["stream_url"],
                "vidid": vidid,
                "duration_min": str(alpha_result["duration"] // 60) + ":" + str(alpha_result["duration"] % 60).zfill(2),
                "thumb": alpha_result["thumbnail"] or thumbnail,
            }
        else:
            track_details = {
                "title": title,
                "link": yturl,
                "vidid": vidid,
                "duration_min": duration_min,
                "thumb": thumbnail,
            }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> Union[str, List[str], Tuple[str, bool], Tuple[List[str], bool]]:
        if videoid:
            link = self.base + link
        if "playlist?list=" in link or "music.youtube.com" in link:
            return await self._download_playlist(link, mystic, video, songaudio, songvideo, format_id, title)
        else:
            return await self._download_single(link, mystic, video, videoid, songaudio, songvideo, format_id, title)

    async def _download_single(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> Union[str, Tuple[str, bool]]:
        
        if not video and not songvideo:
            try:
                results = VideosSearch(link, limit=1)
                search_result = (await results.next())["result"][0]
                search_title = search_result["title"]
                
                alpha_result = await self.alpha_api.search_and_get_stream_url(search_title)
                if alpha_result and alpha_result.get("stream_url"):
                    return alpha_result["stream_url"], None
            except Exception as e:
                LOGGER(__name__).error(f"AlphaAPI fallback failed: {e}")

        loop = asyncio.get_running_loop()

        def is_restricted() -> bool:
            cookie_file = YouTubeUtils.get_cookie_file()
            return bool(cookie_file and os.path.exists(cookie_file))

        common_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "geo_bypass": True,
            "geo_bypass_country": "IN",
            "concurrent_fragment_downloads": 8,
            "cookiefile": YouTubeUtils.get_cookie_file() if is_restricted() else None,
        }

        def audio_dl():
            opts = {
                **common_opts,
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            x = yt_dlp.YoutubeDL(opts)
            info = x.extract_info(link, download=False)
            xyz = os.path.join("downloads", f"{info['id']}.mp3")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            format_str = "best[height<=720]/bestvideo[height<=720]+bestaudio/best[height<=720]"
            if format_id:
                format_str = format_id
            opts = {
                **common_opts,
                "format": format_str,
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "merge_output_format": "mp4",
                "prefer_ffmpeg": True,
            }
            x = yt_dlp.YoutubeDL(opts)
            info = x.extract_info(link, download=False)
            xyz = os.path.join("downloads", f"{info['id']}.mp4")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            opts = {
                **common_opts,
                "format": formats,
                "outtmpl": fpath,
                "merge_output_format": "mp4",
                "prefer_ffmpeg": True,
            }
            x = yt_dlp.YoutubeDL(opts)
            x.download([link])
            return f"{fpath}.mp4"

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            opts = {
                **common_opts,
                "format": format_id,
                "outtmpl": fpath,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "prefer_ffmpeg": True,
            }
            x = yt_dlp.YoutubeDL(opts)
            x.download([link])
            return f"{fpath.split('%(ext)s')[0]}.mp3"

        if songvideo:
            downloaded_file = await loop.run_in_executor(None, song_video_dl)
            direct = True
        elif songaudio:
            downloaded_file = await loop.run_in_executor(None, song_audio_dl)
            direct = True
        elif video:
            if await is_on_off(1):
                direct = True
                downloaded_file = await loop.run_in_executor(None, video_dl)
            else:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    "--cookies", YouTubeUtils.get_cookie_file(),
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    f"{link}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = None
                else:
                    return
        else:
            direct = True
            downloaded_file = await loop.run_in_executor(None, audio_dl)
        return downloaded_file, direct

    async def _download_playlist(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> Union[List[str], Tuple[List[str], bool]]:
        if "music.youtube.com" in link:
            link = link.replace("music.youtube.com", "www.youtube.com")
        loop = asyncio.get_running_loop()

        def is_restricted() -> bool:
            cookie_file = YouTubeUtils.get_cookie_file()
            return bool(cookie_file and os.path.exists(cookie_file))

        common_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": False,
            "geo_bypass": True,
            "geo_bypass_country": "IN",
            "concurrent_fragment_downloads": 8,
            "cookiefile": YouTubeUtils.get_cookie_file() if is_restricted() else None,
        }

        def playlist_dl(is_video: bool = False):
            format_str = "bestaudio[ext=m4a]/bestaudio/best" if not is_video else "best[height<=720]/bestvideo[height<=720]+bestaudio/best[height<=720]"
            postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}] if not is_video else []
            merge_format = None if not is_video else "mp4"
            outtmpl = "downloads/%(playlist)s/%(id)s.%(ext)s"
            opts = {
                **common_opts,
                "format": format_str,
                "outtmpl": outtmpl,
                "postprocessors": postprocessors,
                "merge_output_format": merge_format,
                "prefer_ffmpeg": True,
            }
            x = yt_dlp.YoutubeDL(opts)
            info = x.extract_info(link, download=False)
            paths = []
            x.download([link])
            for entry in info.get("entries", []):
                vid = entry.get("id")
                for root, dirs, files in os.walk("downloads"):
                    for file in files:
                        if file.startswith(vid):
                            paths.append(os.path.join(root, file))
            return paths

        if songvideo or video:
            downloaded_file = await loop.run_in_executor(None, lambda: playlist_dl(True))
            direct = True if await is_on_off(1) else None
        elif songaudio:
            downloaded_file = await loop.run_in_executor(None, lambda: playlist_dl(False))
            direct = True
        else:
            downloaded_file = await loop.run_in_executor(None, lambda: playlist_dl(False))
            direct = True
        return downloaded_file, direct
