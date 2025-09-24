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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChatWriteForbidden, ChatRestricted, RPCError
from Audify import app

log = logging.getLogger(__name__)

# Store pending relationship requests
pending_requests = {}

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

# Define relationship types and their search terms
RELATIONSHIPS = {
    "husband": {
        "search_term": "husband-wife-love",
        "emoji": "👫",
        "message": "wants you to be their husband",
        "accept_message": "accepted to be husband and wife",
    },
    "wife": {
        "search_term": "wife-love-couple",
        "emoji": "💑",
        "message": "wants you to be their wife",
        "accept_message": "accepted to be husband and wife",
    },
    "brother": {
        "search_term": "brother-sister-rakhi",
        "emoji": "🤝",
        "message": "wants you to be their brother",
        "accept_message": "accepted to be brother and sister",
    },
    "sister": {
        "search_term": "sister-love-family",
        "emoji": "👭",
        "message": "wants you to be their sister",
        "accept_message": "accepted to be brother and sister",
    }
}

async def fetch_relationship_gif(relationship_type: str):
    """Fetch a random GIF based on relationship type by scraping Tenor."""
    try:
        search_term = RELATIONSHIPS[relationship_type]["search_term"]
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
            log.warning("[Tenor Scraper] No GIFs found on page")
            return None

        gif_urls = [img["src"] for img in gif_elements if img["src"]]
        return random.choice(gif_urls) if gif_urls else None
    except Exception as e:
        log.exception("[Relationship] Error fetching GIF: %s", e)
        return None

def html_user_mention(user) -> str:
    """Return an HTML mention for the given user."""
    if not user:
        return "someone"
    name = html.escape(user.first_name or "User", quote=True)
    return f'<a href="tg://user?id={user.id}">{name}</a>'

def build_request_caption(requester, target_user, relationship_type: str) -> str:
    """Build the caption for relationship request."""
    requester_mention = html_user_mention(requester)
    target_mention = html_user_mention(target_user)
    emoji = RELATIONSHIPS[relationship_type]["emoji"]
    message = RELATIONSHIPS[relationship_type]["message"]
    
    return f"{requester_mention} {message} {target_mention} {emoji}\n\n💭 What do you say?"

def build_accept_caption(requester, target_user, relationship_type: str) -> str:
    """Build the caption when relationship is accepted."""
    requester_mention = html_user_mention(requester)
    target_mention = html_user_mention(target_user)
    emoji = RELATIONSHIPS[relationship_type]["emoji"]
    accept_message = RELATIONSHIPS[relationship_type]["accept_message"]
    
    return f"🎉 {target_mention} {accept_message} with {requester_mention} {emoji}"

def create_request_keyboard(request_id: str) -> InlineKeyboardMarkup:
    """Create inline keyboard for accept/reject."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"rel_accept_{request_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rel_reject_{request_id}")
        ]
    ])

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
        log.warning("[Relationship] Chat write restricted: %s", message.chat.id if message.chat else "unknown")
    except RPCError as e:
        log.warning("[Relationship] Telegram RPC error in chat %s: %s", message.chat.id if message.chat else "unknown", e)
    except Exception as e:
        log.exception("[Relationship] Unexpected error sending animation: %s", e)
    return False

async def safe_reply_text(message: Message, text: str, reply_markup=None):
    """Safely reply with text and handle possible errors."""
    try:
        await message.reply_text(
            text, 
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
        return True
    except (ChatWriteForbidden, ChatRestricted):
        log.warning("[Relationship] Chat write restricted (text): %s", message.chat.id if message.chat else "unknown")
    except RPCError as e:
        log.warning("[Relationship] Telegram RPC error (text) in chat %s: %s", message.chat.id if message.chat else "unknown", e)
    except Exception as e:
        log.exception("[Relationship] Unexpected error sending text: %s", e)
    return False

async def safe_edit_message(message: Message, text: str, reply_markup=None):
    """Safely edit message and handle possible errors."""
    try:
        await message.edit_text(
            text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        log.exception("[Relationship] Error editing message: %s", e)
        return False

async def relationship_command(client, message: Message, relationship_type: str):
    """Handle the relationship commands to send appropriate GIFs."""
    if not (message and message.from_user):
        log.info("[Relationship] Ignoring message without from_user in chat %s", message.chat.id if message.chat else "unknown")
        return

    # Check if replying to someone
    if not (message.reply_to_message and message.reply_to_message.from_user):
        await safe_reply_text(message, f"❌ Please reply to someone's message to send a {relationship_type} request!")
        return
    
    target_user = message.reply_to_message.from_user
    requester = message.from_user
    
    # Check if trying to send request to themselves
    if target_user.id == requester.id:
        await safe_reply_text(message, "🙄 You can't send a relationship request to yourself!")
        return
    
    # Generate unique request ID
    request_id = f"{requester.id}_{target_user.id}_{relationship_type}_{random.randint(1000, 9999)}"
    
    # Store the request
    pending_requests[request_id] = {
        "requester": requester,
        "target": target_user,
        "relationship_type": relationship_type,
        "chat_id": message.chat.id,
        "message_id": None
    }
    
    # Build caption and keyboard
    caption = build_request_caption(requester, target_user, relationship_type)
    keyboard = create_request_keyboard(request_id)
    
    log.info(f"[Relationship] Created request {request_id} from {requester.id} to {target_user.id}")
    
    # Send the request message
    sent = await safe_reply_text(message, caption, keyboard)
    if not sent:
        await safe_reply_text(message, "❌ Failed to send the relationship request. Please try again later.")
        # Clean up
        pending_requests.pop(request_id, None)

# Register all relationship commands
@app.on_message(filters.command(["husband", "wife", "brother", "sister"]))
async def handle_relationship_commands(client, message: Message):
    """Handle all relationship commands."""
    command = message.command[0].lower()  # Get the command without the '/'
    if command in RELATIONSHIPS:
        await relationship_command(client, message, command)

# Handle callback queries for accept/reject
@app.on_callback_query(filters.regex(r"^rel_(accept|reject)_"))
async def handle_relationship_callback(client, callback_query: CallbackQuery):
    """Handle accept/reject callbacks for relationship requests."""
    try:
        data = callback_query.data
        log.info(f"[Relationship] Received callback: {data} from user {callback_query.from_user.id}")
        
        # Parse callback data
        parts = data.split("_")
        if len(parts) < 3:
            log.error(f"[Relationship] Invalid callback data format: {data}")
            await callback_query.answer("❌ Invalid request format.", show_alert=True)
            return
            
        action = parts[1]  # "accept" or "reject"
        request_id = "_".join(parts[2:])  # everything after "rel_action_"
        
        log.info(f"[Relationship] Parsed action: {action}, request_id: {request_id}")
        
        # Check if request exists
        if request_id not in pending_requests:
            log.warning(f"[Relationship] Request not found: {request_id}")
            await callback_query.answer("❌ This request has expired or is invalid.", show_alert=True)
            return
        
        request_data = pending_requests[request_id]
        requester = request_data["requester"]
        target = request_data["target"]
        relationship_type = request_data["relationship_type"]
        
        log.info(f"[Relationship] Found request: {requester.id} -> {target.id} ({relationship_type})")
        
        # Check if the person clicking is the target
        if callback_query.from_user.id != target.id:
            log.warning(f"[Relationship] Unauthorized callback from {callback_query.from_user.id}, expected {target.id}")
            await callback_query.answer("❌ Only the person who received the request can respond.", show_alert=True)
            return
        
        if action == "accept":
            log.info(f"[Relationship] Processing accept for request {request_id}")
            
            # Fetch GIF for acceptance
            gif_url = await fetch_relationship_gif(relationship_type)
            if gif_url:
                # Build acceptance caption
                caption = build_accept_caption(requester, target, relationship_type)
                
                # Edit message to show GIF
                try:
                    await callback_query.message.delete()
                    await callback_query.message.reply_animation(
                        animation=gif_url,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                    log.info(f"[Relationship] Successfully sent acceptance GIF for request {request_id}")
                except Exception as e:
                    log.exception(f"[Relationship] Error sending acceptance GIF: {e}")
                    # Fallback to text
                    await safe_edit_message(
                        callback_query.message, 
                        caption
                    )
            else:
                # Fallback to text if GIF fails
                caption = build_accept_caption(requester, target, relationship_type)
                await safe_edit_message(callback_query.message, caption)
                log.info(f"[Relationship] Sent acceptance text for request {request_id}")
                
            await callback_query.answer("✅ Request accepted!", show_alert=False)
            
        elif action == "reject":
            log.info(f"[Relationship] Processing reject for request {request_id}")
            
            requester_mention = html_user_mention(requester)
            target_mention = html_user_mention(target)
            emoji = RELATIONSHIPS[relationship_type]["emoji"]
            
            reject_text = f"💔 {target_mention} rejected {requester_mention}'s {relationship_type} request {emoji}"
            await safe_edit_message(callback_query.message, reject_text)
            await callback_query.answer("❌ Request rejected.", show_alert=False)
            log.info(f"[Relationship] Processed rejection for request {request_id}")
        
        # Clean up the request
        pending_requests.pop(request_id, None)
        log.info(f"[Relationship] Cleaned up request {request_id}")
        
    except Exception as e:
        log.exception(f"[Relationship] Error handling relationship callback: {e}")
        await callback_query.answer("❌ An error occurred. Please try again.", show_alert=True)
