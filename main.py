"""
Entry point.

    python main.py

Flow:
  1. bot client starts (loads app/plugins/*)
  2. assistant client starts (string session)
  3. PyTgCalls starts and starts listening for stream-end events
"""

from __future__ import annotations

import asyncio
import logging
import sys

from pyrogram import idle
from pytgcalls import filters as call_filters

import config
from app import player
from app.clients import assistant, bot, call
from app.queue import format_duration, get_queue

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pytgcalls").setLevel(logging.WARNING)
log = logging.getLogger("stranger-music")


@call.on_update(call_filters.stream_end())
async def on_stream_end(client, update) -> None:
    """Auto-play the next queued track when one finishes."""
    chat_id = update.chat_id
    queue = get_queue(chat_id)

    # Guard against double events (audio + video stream ending together)
    if not queue.stream_active:
        return
    queue.stream_active = False

    if queue.loop and queue.current:
        track = queue.current
        try:
            await player.play_track(chat_id, track)
            await bot.send_message(
                chat_id,
                f"🔁 **Repeating:** [{track.title}]({track.url})",
                disable_web_page_preview=True,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("Loop replay failed in %s: %s", chat_id, exc)
        return

    if not queue.tracks:
        await player.stop_stream(chat_id)
        await bot.send_message(
            chat_id,
            f"✅ **Queue khatam.** `{format_duration(0)}` — VC se leave kar diya.",
        )
        return

    nxt = await player.play_next(chat_id)
    if not nxt:
        return

    from app.utils import player_keyboard, track_caption

    await bot.send_message(
        chat_id,
        track_caption(nxt, "🎶 **Now playing**"),
        reply_markup=player_keyboard(),
        disable_web_page_preview=True,
    )


async def main() -> None:
    config.validate()

    log.info("Starting bot client…")
    await bot.start()
    bot_me = await bot.get_me()
    log.info("Bot: @%s", bot_me.username)

    log.info("Starting assistant client…")
    await assistant.start()
    assistant_me = await assistant.get_me()
    log.info("Assistant: %s (id=%s)", assistant_me.first_name, assistant_me.id)

    log.info("Starting PyTgCalls…")
    await call.start()

    log.info("✅ %s is up. Assistant ko group me add karna mat bhoolna.", config.BOT_NAME)
    await idle()

    log.info("Shutting down…")
    await assistant.stop()
    await bot.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Stopped by user.")
