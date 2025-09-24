from pyrogram.types import InlineKeyboardButton

import config
from Audify import app

def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true&admin=delete_messages+invite_users"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true&admin=delete_messages+invite_users",
            )
        ],
        [
            InlineKeyboardButton(text=_["S_B_6"], url=config.SUPPORT_CHANNEL),
            InlineKeyboardButton(
                text=_["S_B_13"],
                url=f"https://t.me/{app.username}?startapp=true",
            ),           
        ],
    ]      
    return buttons
