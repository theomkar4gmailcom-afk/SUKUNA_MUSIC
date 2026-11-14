"""/stats — bot + queue overview (sudoers only)."""

from __future__ import annotations

import platform
import time

from pyrogram import filters
from pyrogram.types import Message

import config
from app.clients import bot
from app.queue import QUEUES

START_TIME = time.time()


@bot.on_message(filters.command(["stats", "ping"], prefixes=config.COMMAND_PREFIXES))
async def stats_handler(client, message: Message) -> None:
    if not message.from_user or message.from_user.id not in config.SUDOERS:
        return

    uptime = int(time.time() - START_TIME)
    active = sum(1 for q in QUEUES.values() if q.stream_active)
    queued = sum(len(q.tracks) for q in QUEUES.values())
    users = len(QUEUES)

    await message.reply_text(
        "**📊 Bot stats**\n"
        f"• Uptime: `{uptime // 3600}h {(uptime % 3600) // 60}m`\n"
        f"• Python: `{platform.python_version()}`\n"
        f"• Chats tracked: `{users}`\n"
        f"• Active streams: `{active}`\n"
        f"• Tracks waiting: `{queued}`"
    )
