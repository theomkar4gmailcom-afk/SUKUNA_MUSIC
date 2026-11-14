"""/queue and /current — read-only info for everyone."""

from __future__ import annotations

from pyrogram import filters
from pyrogram.types import Message

import config
from app import player
from app.clients import bot
from app.queue import format_duration, get_queue, queue_text
from app.utils import player_keyboard


@bot.on_message(filters.command(["queue", "q"], prefixes=config.COMMAND_PREFIXES))
async def queue_handler(client, message: Message) -> None:
    await message.reply_text(
        queue_text(message.chat.id),
        disable_web_page_preview=True,
        reply_markup=player_keyboard(),
    )


@bot.on_message(filters.command(["current", "nowplaying", "np"], prefixes=config.COMMAND_PREFIXES))
async def current_handler(client, message: Message) -> None:
    queue = get_queue(message.chat.id)
    if not queue.current:
        await message.reply_text("❌ Abhi kuch play nahi ho raha.")
        return

    played = await player.played_time(message.chat.id)
    played_seconds = getattr(played, "played_time", 0) or 0

    track = queue.current
    text = (
        f"🎶 **{(track.title)}**\n"
        f"⏱ `{format_duration(played_seconds)}` / `{track.pretty_duration}`\n"
        f"🔗 [link]({track.url})\n"
        f"🙋 {track.requested_by or '—'}\n"
        f"{'⏸ Paused' if queue.paused else '▶️ Playing'} • "
        f"🔁 Loop {'on' if queue.loop else 'off'}"
    )
    await message.reply_text(
        text, disable_web_page_preview=True, reply_markup=player_keyboard()
    )
