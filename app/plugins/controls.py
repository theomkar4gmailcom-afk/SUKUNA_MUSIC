"""/pause /resume /skip /end /loop /volume"""

from __future__ import annotations

from pyrogram import filters
from pyrogram.types import Message

import config
from app import player
from app.clients import bot
from app.queue import get_queue
from app.utils import is_admin, player_keyboard


async def _guard(message: Message) -> bool:
    """Common checks: admin rights + something actually playing."""
    if not message.from_user or not await is_admin(
        message.chat.id, message.from_user.id
    ):
        await message.reply_text("⛔ Sirf group admins music control kar sakte hain.")
        return False
    queue = get_queue(message.chat.id)
    if not queue.current:
        await message.reply_text("❌ Abhi kuch play nahi ho raha.")
        return False
    return True


@bot.on_message(filters.command(["pause"], prefixes=config.COMMAND_PREFIXES) & filters.group)
async def pause_handler(client, message: Message) -> None:
    if not await _guard(message):
        return
    queue = get_queue(message.chat.id)
    if queue.paused:
        await message.reply_text("⏸ Pehle se paused hai.")
        return
    await player.pause_stream(message.chat.id)
    await message.reply_text("⏸ **Paused.**", reply_markup=player_keyboard())


@bot.on_message(filters.command(["resume", "unpause", "r"], prefixes=config.COMMAND_PREFIXES) & filters.group)
async def resume_handler(client, message: Message) -> None:
    if not await _guard(message):
        return
    queue = get_queue(message.chat.id)
    if not queue.paused:
        await message.reply_text("▶️ Already playing.")
        return
    await player.resume_stream(message.chat.id)
    await message.reply_text("▶️ **Resumed.**", reply_markup=player_keyboard())


@bot.on_message(filters.command(["skip", "next", "s"], prefixes=config.COMMAND_PREFIXES) & filters.group)
async def skip_handler(client, message: Message) -> None:
    if not await _guard(message):
        return
    chat_id = message.chat.id
    queue = get_queue(chat_id)

    nxt = await player.play_next(chat_id)
    if not nxt:
        await message.reply_text("⏹ Queue khatam. Voice chat se leave kar diya.")
        return
    from app.utils import track_caption

    await message.reply_text(
        track_caption(nxt, "⏭ **Skipped — now playing**"),
        reply_markup=player_keyboard(),
        disable_web_page_preview=True,
    )


@bot.on_message(filters.command(["end", "stop", "leave"], prefixes=config.COMMAND_PREFIXES) & filters.group)
async def end_handler(client, message: Message) -> None:
    if not message.from_user or not await is_admin(
        message.chat.id, message.from_user.id
    ):
        await message.reply_text("⛔ Sirf group admins music control kar sakte hain.")
        return
    await player.stop_stream(message.chat.id)
    await message.reply_text("⏹ **Playback band, queue clear, VC se leave.**")


@bot.on_message(filters.command(["loop"], prefixes=config.COMMAND_PREFIXES) & filters.group)
async def loop_handler(client, message: Message) -> None:
    if not await _guard(message):
        return
    queue = get_queue(message.chat.id)
    queue.loop = not queue.loop
    state = "on 🔁" if queue.loop else "off"
    await message.reply_text(f"**Loop {state}**")


@bot.on_message(filters.command(["volume", "vol"], prefixes=config.COMMAND_PREFIXES) & filters.group)
async def volume_handler(client, message: Message) -> None:
    if not await _guard(message):
        return
    if len(message.command) < 2:
        await message.reply_text(
            f"Usage: `{config.COMMAND_PREFIXES[0]}volume <1-200>`"
        )
        return
    try:
        volume = int(message.command[1])
    except ValueError:
        await message.reply_text("❌ Number do, jaise `/volume 120`.")
        return
    if not 1 <= volume <= 200:
        await message.reply_text("❌ Volume 1 se 200 ke beech hona chahiye.")
        return
    await player.set_volume(message.chat.id, volume)
    await message.reply_text(f"🔊 Volume set to **{volume}%**")
