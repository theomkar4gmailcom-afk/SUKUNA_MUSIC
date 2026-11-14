"""Inline button handlers (player panel + /search results)."""

from __future__ import annotations

from pyrogram import filters
from pyrogram.types import CallbackQuery

import config
from app import cache, player
from app.clients import bot
from app.queue import get_queue, queue_text
from app.utils import is_admin, player_keyboard, track_caption


@bot.on_callback_query(filters.regex(r"^help$"))
async def help_cb(client, query: CallbackQuery) -> None:
    from app.plugins.start import HELP_TEXT

    await query.message.reply_text(
        HELP_TEXT.format(
            bot=config.BOT_NAME,
            p=config.COMMAND_PREFIXES[0],
            n=config.SEARCH_LIMIT,
        )
    )
    await query.answer()


@bot.on_callback_query(filters.regex(r"^player "))
async def player_cb(client, query: CallbackQuery) -> None:
    action = query.data.split(" ", 1)[1]
    chat_id = query.message.chat.id

    if not await is_admin(chat_id, query.from_user.id):
        await query.answer("⛔ Sirf group admins control kar sakte hain.", show_alert=True)
        return

    queue = get_queue(chat_id)

    if action == "pause":
        if not queue.current:
            await query.answer("Kuch play nahi ho raha.", show_alert=True)
        elif queue.paused:
            await query.answer("Pehle se paused hai.")
        else:
            await player.pause_stream(chat_id)
            await query.answer("⏸ Paused")
            await query.message.edit_reply_markup(player_keyboard())

    elif action == "resume":
        if not queue.paused:
            await query.answer("Already playing.")
        else:
            await player.resume_stream(chat_id)
            await query.answer("▶️ Resumed")
            await query.message.edit_reply_markup(player_keyboard())

    elif action == "skip":
        nxt = await player.play_next(chat_id)
        await query.answer("⏭ Skipped" if nxt else "Queue khali hai")
        if nxt:
            await query.message.reply_text(
                track_caption(nxt, "⏭ **Now playing**"),
                reply_markup=player_keyboard(),
                disable_web_page_preview=True,
            )

    elif action == "stop":
        await player.stop_stream(chat_id)
        await query.answer("⏹ Stopped")
        try:
            await query.message.edit_text("⏹ **Playback band, queue clear.**")
        except Exception:
            pass

    elif action == "loop":
        queue.loop = not queue.loop
        await query.answer(f"Loop {'on 🔁' if queue.loop else 'off'}")
        await query.message.edit_reply_markup(player_keyboard())

    elif action == "queue":
        await query.answer()
        await query.message.reply_text(
            queue_text(chat_id), disable_web_page_preview=True
        )


@bot.on_callback_query(filters.regex(r"^pick "))
async def pick_cb(client, query: CallbackQuery) -> None:
    _, token, index_raw = query.data.split()
    index = int(index_raw)
    chat_id = query.message.chat.id

    if index < 0:
        cache.pop(token)
        await query.answer("Cancelled")
        try:
            await query.message.edit_text("❌ Search cancel kar diya.")
        except Exception:
            pass
        return

    if not await is_admin(chat_id, query.from_user.id):
        await query.answer("⛔ Sirf group admins play kar sakte hain.", show_alert=True)
        return

    tracks = cache.get(token)
    if not tracks or index >= len(tracks):
        await query.answer("Results expire ho gaye, dobara /search karo.", show_alert=True)
        return

    track = tracks[index]
    user = query.from_user
    track.requested_by = f"[{user.first_name or 'User'}](tg://user?id={user.id})"
    track.requested_by_id = user.id

    queue = get_queue(chat_id)
    if queue.stream_active or queue.current:
        queue.add(track)
        await query.answer("➕ Queue me add kiya")
        await query.message.reply_text(
            f"➕ **Queued:** [{track.title}]({track.url}) — `{track.pretty_duration}`",
            disable_web_page_preview=True,
        )
        return

    await player.play_track(chat_id, track)
    await query.answer("▶️ Playing")
    await query.message.reply_text(
        track_caption(track),
        reply_markup=player_keyboard(),
        disable_web_page_preview=True,
    )
