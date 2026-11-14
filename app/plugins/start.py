"""/start, /help, /id"""

from __future__ import annotations

from pyrogram import filters
from pyrogram.types import Message

import config
from app.clients import bot
from app.utils import start_keyboard

HELP_TEXT = """
**{bot} — commands**

**Playback**
• `{p}play <name/link>` — song ya video VC me play karo
• `{p}vplay <name/link>` — video ke saath play
• `{p}playlist <playlist link>` — pura playlist queue me
• `{p}search <name>` — top {n} results, button se choose karo
• `{p}play` (audio/video file ko reply karke) — Telegram file play

**Controls** (admins only)
• `{p}pause` / `{p}resume`
• `{p}skip` — next track
• `{p}end` — stop + clear queue + leave VC
• `{p}loop` — current track repeat on/off
• `{p}volume 1-200`

**Info**
• `{p}queue` — queue dekho
• `{p}current` — now playing + elapsed time

**Setup:** assistant account ko group me add karo, phir group voice chat
start karke `/play` bhejo.
""".strip()


@bot.on_message(filters.command(["start"], prefixes=config.COMMAND_PREFIXES))
async def start_handler(client, message: Message) -> None:
    name = message.from_user.first_name if message.from_user else "there"
    text = (
        f"👋 **Hey {name}!**\n\n"
        f"Main **{config.BOT_NAME}** hoon — group voice chat me gaane play karta hoon.\n\n"
        f"➊ Mujhe aur mere assistant account ko group me add karo\n"
        f"➋ Group voice chat start karo\n"
        f"➌ `{config.COMMAND_PREFIXES[0]}play <song name>` bhejo\n\n"
        f"Commands ke liye /help"
    )
    if config.START_IMAGE:
        try:
            await message.reply_photo(
                config.START_IMAGE, caption=text, reply_markup=start_keyboard()
            )
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=start_keyboard())


@bot.on_message(filters.command(["help"], prefixes=config.COMMAND_PREFIXES))
async def help_handler(client, message: Message) -> None:
    await message.reply_text(
        HELP_TEXT.format(
            bot=config.BOT_NAME,
            p=config.COMMAND_PREFIXES[0],
            n=config.SEARCH_LIMIT,
        )
    )


@bot.on_message(filters.command(["id", "chatid"], prefixes=config.COMMAND_PREFIXES))
async def id_handler(client, message: Message) -> None:
    await message.reply_text(
        f"**Chat id:** `{message.chat.id}`\n"
        f"**Your id:** `{message.from_user.id if message.from_user else '—'}`"
    )
