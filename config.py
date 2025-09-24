# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---------------------------------------------------------

import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

# Telegram API Credentials
API_ID = int(getenv("API_ID", "18136872"))
API_HASH = getenv("API_HASH", "312d861b78efcd1b02183b2ab52a83a4")
BOT_TOKEN = getenv("BOT_TOKEN", "")
OWNER_ID = 1852362865
BOT_ID = 8447380400

# Music API Configs
API_URL = getenv("API_URL", "https://your-default-api-domain.com/api") #API Config ~
API_KEY = getenv("API_KEY", None)
DOWNLOADS_DIR = "downloads"
COOKIE_URL = getenv("COOKIE_URL", "https://your-default-api-domain.com/cookies.txt")

# Basic Bot Configs
OWNER_USERNAME = getenv("OWNER_USERNAME", "Allenspark10") #Replace With Yours ~
BOT_USERNAME = getenv("BOT_USERNAME", "deltamusicrobot") #Replace With Yours ~
BOT_NAME = getenv("BOT_NAME", "HanumanMusic") #Replace With Yours ~
ASSUSERNAME = getenv("ASSUSERNAME", "Cutiedelta") #Replace With Yours ~
LOGGER_ID = int(getenv("LOGGER_ID", "-1002436267094")) #Replace With Yours ~
BOT_LOGS_CHANNEL = int(getenv("BOT_LOGS_CHANNEL", "-1002178792923")) #Replace With Yours ~

# MongoDB
MONGO_DB_URI = getenv("MONGO_DB_URI", None)

# Duration
DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", "99999"))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "99999"))
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "99999"))
DURATION_LIMIT = DURATION_LIMIT_MIN * 60

# Auto-leave
AUTO_LEAVING_ASSISTANT = getenv("AUTO_LEAVING_ASSISTANT", "True")
AUTO_LEAVE_ASSISTANT_TIME = int(getenv("ASSISTANT_LEAVE_TIME", "9000"))

# Spotify
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "")

# Heroku (if used)
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME", None)
HEROKU_API_KEY = getenv("HEROKU_API_KEY", None)

# GitHub Upstream
UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/utkarshdubey2008/kawai",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv(
    "GIT_TOKEN", None
)  # Fill this variable if your upstream repository is private

# Support
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/thealphabotz")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/alphabotzchat")
SOURCE_CODE = getenv("SOURCE_CODE", "https://github.com/AlphaBotz/Kawai2.0")
PRIVACY_LINK = getenv("PRIVACY_LINK", "https://graph.org/vTelegraphBot-08-21-15")

# Playlist
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", "9999"))

# File Size Limits
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", "5242880000"))  # ~5GB
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", "5242880000"))

# String Sessions (for assistant accounts)
STRING1 = getenv("STRING_SESSION")
STRING2 = getenv("STRING_SESSION2")
STRING3 = getenv("STRING_SESSION3")
STRING4 = getenv("STRING_SESSION4")
STRING5 = getenv("STRING_SESSION5")
STRING6 = getenv("STRING_SESSION6")
STRING7 = getenv("STRING_SESSION7")

# Pyrogram Filter for Banned Users (empty list for now)
BANNED_USERS = filters.user([])

# Runtime Dicts (used in other modules)
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

# Image URLs
FAILED = "https://files.catbox.moe/site43.jpg"


START_IMG_URL = getenv(
    "START_IMG_URL", "https://files.catbox.moe/73294o.jpg"
)
PING_IMG_URL = getenv(
    "PING_IMG_URL", "https://files.catbox.moe/87vutp.jpg"
)
PLAYLIST_IMG_URL = "https://files.catbox.moe/87vutp.jpg"
STATS_IMG_URL = "https://files.catbox.moe/87vutp.jpg"
TELEGRAM_AUDIO_URL = "https://files.catbox.moe/55e9iq.jpg"
TELEGRAM_VIDEO_URL = "https://files.catbox.moe/55e9iq.jpg"
STREAM_IMG_URL = "https://files.catbox.moe/73294o.jpg"
SOUNCLOUD_IMG_URL = "https://files.catbox.moe/87vutp.jpg"
YOUTUBE_IMG_URL = "https://files.catbox.moe/55e9iq.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://files.catbox.moe/73294o.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://files.catbox.moe/73294o.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://files.catbox.moe/73294o.jpg"

# Helper Function
def time_to_seconds(time: str) -> int:
    return sum(int(x) * 60**i for i, x in enumerate(reversed(time.split(":"))))

# URL Validations
if SUPPORT_CHANNEL and not re.match(r"(?:http|https)://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - SUPPORT_CHANNEL must start with http:// or https://")

if SUPPORT_CHAT and not re.match(r"(?:http|https)://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] - SUPPORT_CHAT must start with http:// or https://")

if SOURCE_CODE and not re.match(r"(?:http|https)://", SOURCE_CODE):
    raise SystemExit("[ERROR] - SOURCE_CODE must start with http:// or https://")
