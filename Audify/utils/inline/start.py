from pyrogram.types import InlineKeyboardButton

import config
from Audify import app

def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
            # Removed Support Chat button here
        ],
    ]
    return buttons

def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_4"], callback_data="settings_back_helper"
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_6"], url=config.SUPPORT_CHANNEL
            ),
            # Removed Support Chat button here
        ],
        [
            InlineKeyboardButton(
                text="Mini App 🎧", url=f"https://t.me/{app.username}?startapp"
            ),
            # Removed Source Code button here
        ],
    ]
    return buttons
