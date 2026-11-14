"""Shared helpers: permission checks, keyboards, small formatting utils."""

from __future__ import annotations

from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from app.clients import bot


# --------------------------------------------------------------- permissions
async def is_admin(chat_id: int, user_id: int) -> bool:
    """True if the user may control playback (group admin / sudoer / owner)."""
    if user_id in config.SUDOERS:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False
    if member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
        return True
    privileges = getattr(member, "privileges", None)
    return bool(privileges and getattr(privileges, "manage_video_chats", False))


async def in_group(message: Message) -> bool:
    return message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)


# ------------------------------------------------------------------ keyboards
def player_keyboard(stop_label: str = "⏹ End") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏸ Pause", callback_data="player pause"),
                InlineKeyboardButton("▶️ Resume", callback_data="player resume"),
            ],
            [
                InlineKeyboardButton("⏭ Skip", callback_data="player skip"),
                InlineKeyboardButton(stop_label, callback_data="player stop"),
            ],
            [
                InlineKeyboardButton("🔁 Loop", callback_data="player loop"),
                InlineKeyboardButton("📜 Queue", callback_data="player queue"),
            ],
        ]
    )


def search_keyboard(token: str, count: int) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for index in range(count):
        row.append(
            InlineKeyboardButton(f"{index + 1}", callback_data=f"pick {token} {index}")
        )
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("❌ Cancel", callback_data=f"pick {token} -1")])
    return InlineKeyboardMarkup(rows)


def start_keyboard() -> InlineKeyboardMarkup:
    rows = []
    if config.BUTTON_ADD_GROUP:
        rows.append(
            [InlineKeyboardButton("➕ Add me to a group", url=config.BUTTON_ADD_GROUP)]
        )
    if config.BUTTON_CHANNEL:
        rows.append([InlineKeyboardButton("📣 Updates", url=config.BUTTON_CHANNEL)])
    rows.append([InlineKeyboardButton("❓ Help", callback_data="help")])
    return InlineKeyboardMarkup(rows)


# ------------------------------------------------------------------ formatting
def mention(user_id: int, name: str) -> str:
    return f"[{name}](tg://user?id={user_id})"


def track_caption(track, header: str = "🎶 **Now playing**") -> str:
    parts = [
        header,
        f"🎵 [{track.title}]({track.url})",
        f"⏱ `{track.pretty_duration}`",
    ]
    if track.requested_by:
        parts.append(f"🙋 by {track.requested_by}")
    return "\n".join(parts)


async def safe_edit(message: Message, text: str, **kwargs) -> None:
    try:
        await message.edit_text(text, **kwargs)
    except Exception:
        pass


async def safe_reply(message: Message, text: str, **kwargs) -> Message | None:
    try:
        return await message.reply_text(text, **kwargs)
    except Exception:
        return None
