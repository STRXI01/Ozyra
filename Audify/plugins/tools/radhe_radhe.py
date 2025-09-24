# ---------------------------------------------------------
# Audify Bot - All rights reserved
# ---------------------------------------------------------
# This code is part of the Audify Bot project.
# Unauthorized copying, distribution, or use is prohibited.
# © Graybots™. All rights reserved.
# ---------------------------------------------------------

import logging
import html
import random
import requests
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from pyrogram.errors import ChatWriteForbidden, ChatRestricted, RPCError
from Audify import app

log = logging.getLogger(__name__)

# Prepare a requests session with automatic retries
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[502, 503, 504, 522, 524],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Define patterns for matching "Radhe Radhe" variations
def create_radhe_pattern():
    """Create a regex pattern that matches various forms of 'Radhe Radhe'"""
    base = r'radhe\s*[_\s]*radhe'  # Matches: radhe radhe, radhe_radhe
    # Add optional emojis before, after, or between words
    emoji_pattern = r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]*'
    pattern = f'{emoji_pattern}{base}{emoji_pattern}'
    return re.compile(pattern, re.IGNORECASE)

RADHE_PATTERN = create_radhe_pattern()

async def fetch_radha_krishna_gif():
    """Fetch a random Radha-Krishna GIF by scraping Tenor."""
    try:
        url = "https://tenor.com/search/radha-krishna-gifs"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = session.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            log.warning("[Tenor Scraper] Failed to fetch GIF page: %s", r.status_code)
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        gif_elements = soup.select("div.Gif img[src*='.gif']")
        if not gif_elements:
            log.warning("[Tenor Scraper] No GIFs found on page")
            return None

        gif_urls = [img["src"] for img in gif_elements if img["src"]]
        return random.choice(gif_urls) if gif_urls else None
    except Exception as e:
        log.exception("[Tenor Scraper] Error fetching GIF: %s", e)
        return None

def html_user_mention(user) -> str:
    """Return an HTML mention for the given user."""
    if not user:
        return "someone"
    name = html.escape(user.first_name or "User", quote=True)
    return f'<a href="tg://user?id={user.id}">{name}</a>'

def build_caption(sender, replied_user=None) -> str:
    """Build the caption with user mention for the Radhe Radhe GIF."""
    sender_mention = html_user_mention(sender)
    emoji = "🌺"
    if replied_user:
        replied_mention = html_user_mention(replied_user)
        return f"{sender_mention} chants <b>Radhe Radhe</b> to {replied_mention} {emoji}"
    return f"{sender_mention} chants <b>Radhe Radhe</b> {emoji}"

async def safe_reply_animation(message: Message, animation_url: str, caption: str):
    """Safely reply with an animation and handle possible errors."""
    try:
        await message.reply_animation(
            animation=animation_url,
            caption=caption,
            parse_mode=ParseMode.HTML,
            disable_notification=False
        )
        return True
    except (ChatWriteForbidden, ChatRestricted):
        log.warning("[RadheRadhe] Chat write restricted: %s", message.chat.id if message.chat else "unknown")
    except RPCError as e:
        log.warning("[RadheRadhe] Telegram RPC error in chat %s: %s", message.chat.id if message.chat else "unknown", e)
    except Exception as e:
        log.exception("[RadheRadhe] Unexpected error sending animation: %s", e)
    return False

async def safe_reply_text(message: Message, text: str):
    """Safely reply with text and handle possible errors."""
    try:
        await message.reply_text(text, disable_web_page_preview=True)
        return True
    except (ChatWriteForbidden, ChatRestricted):
        log.warning("[RadheRadhe] Chat write restricted (text): %s", message.chat.id if message.chat else "unknown")
    except RPCError as e:
        log.warning("[RadheRadhe] Telegram RPC error (text) in chat %s: %s", message.chat.id if message.chat else "unknown", e)
    except Exception as e:
        log.exception("[RadheRadhe] Unexpected error sending text: %s", e)
    return False

async def radhe_radhe_command(client, message: Message):
    """Handle the Radhe Radhe messages to send a Radha-Krishna GIF."""
    if not (message and message.from_user):
        log.info("[RadheRadhe] Ignoring message without from_user in chat %s", message.chat.id if message.chat else "unknown")
        return

    # Fetch GIF
    gif_url = await fetch_radha_krishna_gif()
    if not gif_url:
        await safe_reply_text(message, "❌ Failed to fetch a Radha-Krishna GIF.")
        return

    # Build caption
    replied_user = message.reply_to_message.from_user if (message.reply_to_message and message.reply_to_message.from_user) else None
    caption = build_caption(message.from_user, replied_user)

    # Send GIF with caption
    sent = await safe_reply_animation(message, gif_url, caption)
    if not sent:
        await safe_reply_text(message, "❌ Failed to send the GIF. Please try again later.")

# Register both command and text triggers
@app.on_message(
    filters.command("radhe_radhe") |
    filters.regex(RADHE_PATTERN)
)
async def radhe_radhe_handler(client, message: Message):
    await radhe_radhe_command(client, message)
