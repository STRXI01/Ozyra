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
import asyncio
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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

# Define the fuck command configuration
FUCK_CONFIG = {
    "search_term": "adult-couple-intimate",
    "emoji": "🔥",
    "message": "wants to get spicy with",
    "accept_search_term": "intimate-couple-18+",
    "baby_search_term": "newborn-baby-cute",
}

# List of random Indian names for the baby
INDIAN_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Ananya", "Diya", "Isha", "Aarohi", "Anika", "Pari",
    "Saanvi", "Navya", "Aadya", "Kiara"
]

async def fetch_gif(search_term: str):
    """Fetch a random GIF based on the provided search term by scraping Tenor."""
    try:
        url = f"https://tenor.com/search/{search_term}-gifs"
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
            log.warning("[Tenor Scraper] No GIFs found on page for term: %s", search_term)
            return None

        gif_urls = [img["src"] for img in gif_elements if img["src"]]
        return random.choice(gif_urls) if gif_urls else None
    except Exception as e:
        log.exception("[Fuck Command] Error fetching GIF for term %s: %s", search_term, e)
        return None

def html_user_mention(user) -> str:
    """Return an HTML mention for the given user."""
    if not user:
        return "someone"
    name = html.escape(user.first_name or "User", quote=True)
    return f'<a href="tg://user?id={user.id}">{name}</a>'

def build_caption(sender, replied_user=None) -> str:
    """Build the caption with user mention for the fuck command GIF."""
    sender_mention = html_user_mention(sender)
    emoji = FUCK_CONFIG["emoji"]
    message = FUCK_CONFIG["message"]
    
    if replied_user:
        replied_mention = html_user_mention(replied_user)
        return f"{sender_mention} {message} {replied_mention} {emoji}"
    return f"{sender_mention} is looking for some spice {emoji}"

async def safe_reply_animation(message: Message, animation_url: str, caption: str, reply_markup=None):
    """Safely reply with an animation and handle possible errors."""
    try:
        await message.reply_animation(
            animation=animation_url,
            caption=caption,
            parse_mode=ParseMode.HTML,
            disable_notification=False,
            reply_markup=reply_markup
        )
        return True
    except (ChatWriteForbidden, ChatRestricted):
        log.warning("[Fuck Command] Chat write restricted: %s", message.chat.id if message.chat else "unknown")
    except RPCError as e:
        log.warning("[Fuck Command] Telegram RPC error in chat %s: %s", message.chat.id if message.chat else "unknown", e)
    except Exception as e:
        log.exception("[Fuck Command] Unexpected error sending animation: %s", e)
    return False

async def safe_reply_text(message: Message, text: str):
    """Safely reply with text and handle possible errors."""
    try:
        await message.reply_text(text, disable_web_page_preview=True)
        return True
    except (ChatWriteForbidden, ChatRestricted):
        log.warning("[Fuck Command] Chat write restricted (text): %s", message.chat.id if message.chat else "unknown")
    except RPCError as e:
        log.warning("[Fuck Command] Telegram RPC error (text) in chat %s: %s", message.chat.id if message.chat else "unknown", e)
    except Exception as e:
        log.exception("[Fuck Command] Unexpected error sending text: %s", e)
    return False

@app.on_message(filters.command("fuck"))
async def fuck_command(client, message: Message):
    """Handle the /fuck command to send an 18+ GIF with accept/decline buttons."""
    if not (message and message.from_user):
        log.info("[Fuck Command] Ignoring message without from_user in chat %s", message.chat.id if message.chat else "unknown")
        return

    # Ensure a reply to a user
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await safe_reply_text(message, "❌ Please reply to a user's message to use this command!")
        return

    # Fetch initial 18+ GIF
    gif_url = await fetch_gif(FUCK_CONFIG["search_term"])
    if not gif_url:
        await safe_reply_text(message, "❌ Failed to fetch an intimate GIF.")
        return

    # Build caption
    replied_user = message.reply_to_message.from_user
    caption = build_caption(message.from_user, replied_user)

    # Add inline buttons
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Accept", callback_data=f"fuck_accept_{message.from_user.id}_{replied_user.id}_{message.id}"),
            InlineKeyboardButton("Decline", callback_data=f"fuck_decline_{message.from_user.id}_{replied_user.id}_{message.id}")
        ]
    ])

    # Send GIF with caption and buttons
    sent = await safe_reply_animation(message, gif_url, caption, reply_markup)
    if not sent:
        await safe_reply_text(message, "❌ Failed to send the GIF. Please try again later.")

@app.on_callback_query(filters.regex(r"^fuck_(accept|decline)_(\d+)_(\d+)_(\d+)$"))
async def handle_fuck_response(client, callback_query: CallbackQuery):
    """Handle the accept/decline button presses for the /fuck command."""
    action = callback_query.matches[0].group(1)  # accept or decline
    sender_id = int(callback_query.matches[0].group(2))
    replied_user_id = int(callback_query.matches[0].group(3))
    message_id = int(callback_query.matches[0].group(4))

    # Check if the user pressing the button is the replied-to user
    if callback_query.from_user.id != replied_user_id:
        await callback_query.answer("Only the tagged user can respond to this!", show_alert=True)
        return

    # Handle Decline
    if action == "decline":
        decline_caption = f"{html_user_mention(callback_query.from_user)} politely declined the offer! 😅"
        await safe_reply_text(callback_query.message, decline_caption)
        await callback_query.message.edit_reply_markup(None)  # Remove buttons
        return

    # Handle Accept
    # Fetch a new 18+ GIF
    accept_gif_url = await fetch_gif(FUCK_CONFIG["accept_search_term"])
    if not accept_gif_url:
        await safe_reply_text(callback_query.message, "❌ Failed to fetch an intimate GIF.")
        await callback_query.message.edit_reply_markup(None)
        return

    accept_caption = f"{html_user_mention(callback_query.from_user)} accepted {html_user_mention(await client.get_users(sender_id))}’s proposal! Things are heating up! 🔥"
    sent = await safe_reply_animation(callback_query.message, accept_gif_url, accept_caption)
    await callback_query.message.edit_reply_markup(None)  # Remove buttons

    if not sent:
        await safe_reply_text(callback_query.message, "❌ Failed to send the intimate GIF.")
        return

    # Wait 9 seconds
    await asyncio.sleep(9)

    # Fetch a newborn baby GIF
    baby_gif_url = await fetch_gif(FUCK_CONFIG["baby_search_term"])
    if not baby_gif_url:
        await safe_reply_text(callback_query.message, "❌ Failed to fetch a newborn baby GIF.")
        return

    # Generate a random Indian name
    baby_name = random.choice(INDIAN_NAMES)
    baby_caption = f"Congratulations! {html_user_mention(await client.get_users(sender_id))} and {html_user_mention(callback_query.from_user)} welcome their new child, {baby_name}, to the world! 👶🎉"
    
    # Send baby GIF
    sent = await safe_reply_animation(callback_query.message, baby_gif_url, baby_caption)
    if not sent:
        await safe_reply_text(callback_query.message, "❌ Failed to send the newborn baby GIF.")
