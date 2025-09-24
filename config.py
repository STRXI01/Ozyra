import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

API_ID = int(getenv("API_ID", "27696582"))
API_HASH = getenv("API_HASH", "45fccefb72a57ff1b858339774b6d005")
BOT_TOKEN = getenv("BOT_TOKEN", "")
OWNER_ID = 7639428220
BOT_ID = 7073582508


API_URL = getenv("API_URL", "https://your-default-api-domain.com/api")
API_KEY = getenv("API_KEY", None)
DOWNLOADS_DIR = "downloads"
COOKIE_URL = getenv("COOKIE_URL", "https://your-default-api-domain.com/cookies.txt")

OWNER_USERNAME = getenv("OWNER_USERNAME", "Synckex")
BOT_USERNAME = getenv("BOT_USERNAME", "StormMusicPlayer_bot")
BOT_NAME = getenv("BOT_NAME", "Տᴛᴏʀᴍ")
ASSUSERNAME = getenv("ASSUSERNAME", "")
LOGGER_ID = int(getenv("LOGGER_ID", "-1002139499282"))
BOT_LOGS_CHANNEL = int(getenv("BOT_LOGS_CHANNEL", "-1002384375981"))

MONGO_DB_URI = getenv("MONGO_DB_URI", None)

DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", "99999"))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "99999"))
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "99999"))
DURATION_LIMIT = DURATION_LIMIT_MIN * 60

AUTO_LEAVING_ASSISTANT = getenv("AUTO_LEAVING_ASSISTANT", "True")
AUTO_LEAVE_ASSISTANT_TIME = int(getenv("ASSISTANT_LEAVE_TIME", "9000"))

SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "")

HEROKU_APP_NAME = getenv("HEROKU_APP_NAME", None)
HEROKU_API_KEY = getenv("HEROKU_API_KEY", None)

UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/STRXI01/Ozyra",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv(
    "GIT_TOKEN", None
)

SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/STORM_TECHH")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/STORM_CORE")

PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", "9999"))

TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", "5242880000"))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", "5242880000"))

STRING1 = getenv("STRING_SESSION")
STRING2 = getenv("STRING_SESSION2")
STRING3 = getenv("STRING_SESSION3")
STRING4 = getenv("STRING_SESSION4")
STRING5 = getenv("STRING_SESSION5")
STRING6 = getenv("STRING_SESSION6")
STRING7 = getenv("STRING_SESSION7")

BANNED_USERS = filters.user([])

adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

FAILED = "https://files.catbox.moe/0gfbyb.jpg"


START_IMG_URL = getenv(
    "START_IMG_URL", "https://envs.sh/lSU.jpg"
)
PING_IMG_URL = getenv(
    "PING_IMG_URL", "https://graph.org/file/9077cd2ba5818efef2d28.jpg"
)
PLAYLIST_IMG_URL = getenv("PLAYLIST_IMG_URL", "https://graph.org/file/eb1e2b58e17964083db73.jpg")
STATS_IMG_URL = getenv("STATS_IMG_URL", "https://envs.sh/Ol4.jpg")
TELEGRAM_AUDIO_URL = getenv("TELEGRAM_AUDIO_URL", "https://envs.sh/Olr.jpg")
TELEGRAM_VIDEO_URL = getenv("TELEGRAM_VIDEO_URL", "https://envs.sh/Olr.jpg")
STREAM_IMG_URL = getenv("STREAM_IMG_URL", "https://envs.sh/Olk.jpg")
YOUTUBE_IMG_URL = getenv("YOUTUBE_IMG_URL", "https://files.catbox.moe/6xpaz5.jpg")
FAILED = "https://files.catbox.moe/6xpaz5.jpg"
SOUNCLOUD_IMG_URL = "https://envs.sh/Olk.jpg"
SPOTIFY_ARTIST_IMG_URL = getenv("SPOTIFY_ARTIST_IMG_URL", "https://envs.sh/Olk.jpg")
SPOTIFY_ALBUM_IMG_URL = getenv("SPOTIFY_ALBUM_IMG_URL", "https://envs.sh/Olk.jpg")
SPOTIFY_PLAYLIST_IMG_URL = getenv("SPOTIFY_PLAYLIST_IMG_URL", "https://envs.sh/Olk.jpg")

def time_to_seconds(time: str) -> int:
    return sum(int(x) * 60**i for i, x in enumerate(reversed(time.split(":"))))

if SUPPORT_CHANNEL and not re.match(r"(?:http|https)://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - SUPPORT_CHANNEL must start with http:// or https://")

if SUPPORT_CHAT and not re.match(r"(?:http|https)://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] - SUPPORT_CHAT must start with http:// or https://")
