"""/play, /vplay, /playlist, /search"""

from __future__ import annotations

from pathlib import Path

from pyrogram import filters
from pyrogram.types import Message

import config
from app import cache, downloader, player
from app.clients import bot
from app.queue import Track, get_queue
from app.utils import (
    is_admin,
    mention,
    player_keyboard,
    search_keyboard,
    track_caption,
)

PLAY_CMDS = ["play", "p", "vplay", "vp"]


def _requested_by(message: Message) -> str:
    user = message.from_user
    if not user:
        return "Anonymous"
    return mention(user.id, user.first_name or "User")


def _has_media(message: Message) -> bool:
    replied = message.reply_to_message
    if not replied:
        return False
    return bool(replied.audio or replied.voice or replied.video or replied.document)


async def _track_from_reply(message: Message, is_video: bool) -> Track | None:
    replied = message.reply_to_message
    if not replied:
        return None
    media = replied.audio or replied.voice or replied.video or replied.document
    if not media:
        return None

    suffix = Path(getattr(media, "file_name", "") or "").suffix or ".mp3"
    target = config.DOWNLOAD_DIR / f"{message.chat.id}_{replied.id}{suffix}"
    status_path = await replied.download(file_name=str(target))
    if not status_path:
        return None

    title = (
        getattr(media, "title", None)
        or getattr(media, "file_name", None)
        or "Telegram file"
    )
    return Track(
        title=title,
        url=str(status_path),
        duration=int(getattr(media, "duration", 0) or 0),
        thumbnail=None,
        is_video=is_video or bool(replied.video),
    )


async def _enqueue_or_play(message: Message, status: Message, track: Track) -> None:
    chat_id = message.chat.id
    queue = get_queue(chat_id)

    if queue.stream_active or queue.current:
        queue.add(track)
        await status.edit_text(
            f"➕ **Queue me add kiya** ({len(queue.tracks)})\n"
            f"🎵 [{track.title}]({track.url})\n"
            f"⏱ `{track.pretty_duration}`",
            disable_web_page_preview=True,
        )
        return

    try:
        await player.play_track(chat_id, track)
    except Exception as exc:  # noqa: BLE001
        await status.edit_text(
            "❌ Voice chat join nahi kar paya.\n"
            f"`{type(exc).__name__}: {exc}`\n\n"
            "Check karo: group me voice chat start hai? Assistant account group "
            "ka member hai?"
        )
        return

    await status.edit_text(
        track_caption(track),
        reply_markup=player_keyboard(),
        disable_web_page_preview=True,
    )


@bot.on_message(
    filters.command(PLAY_CMDS, prefixes=config.COMMAND_PREFIXES) & filters.group
)
async def play_handler(client, message: Message) -> None:
    if not message.from_user or not await is_admin(
        message.chat.id, message.from_user.id
    ):
        await message.reply_text("⛔ Sirf group admins music control kar sakte hain.")
        return

    is_video = message.command[0].lower() in ("vplay", "vp")
    query = " ".join(message.command[1:]).strip()
    replied_media = _has_media(message)

    if not query and not replied_media:
        await message.reply_text(
            "**Usage**\n"
            f"`{config.COMMAND_PREFIXES[0]}play <song name>`\n"
            f"`{config.COMMAND_PREFIXES[0]}play <youtube link>`\n"
            f"`{config.COMMAND_PREFIXES[0]}vplay <song>` — video ke saath\n"
            "Ya kisi audio/video file ko reply karke /play bhejo."
        )
        return

    status = await message.reply_text("🔎 Search kar raha hoon…")

    if replied_media and not query:
        track = await _track_from_reply(message, is_video)
        if not track:
            await status.edit_text("❌ File download nahi ho payi.")
            return
        track.requested_by = _requested_by(message)
        track.requested_by_id = message.from_user.id
        await _enqueue_or_play(message, status, track)
        return

    tracks = await downloader.search(query, limit=1, is_video=is_video)
    if not tracks:
        await status.edit_text(
            "❌ Kuch nahi mila. Spelling check karo ya seedha YouTube link do."
        )
        return

    track = tracks[0]
    track.requested_by = _requested_by(message)
    track.requested_by_id = message.from_user.id
    await _enqueue_or_play(message, status, track)


@bot.on_message(
    filters.command(["search", "song"], prefixes=config.COMMAND_PREFIXES)
    & filters.group
)
async def search_handler(client, message: Message) -> None:
    query = " ".join(message.command[1:]).strip()
    if not query:
        await message.reply_text(
            f"Usage: `{config.COMMAND_PREFIXES[0]}search <song name>`"
        )
        return

    status = await message.reply_text("🔎 Searching…")
    tracks = await downloader.search(query, limit=config.SEARCH_LIMIT)
    if not tracks:
        await status.edit_text("❌ Kuch nahi mila.")
        return

    token = cache.store(tracks)
    lines = ["**Search results** — number dabao:"]
    for index, track in enumerate(tracks, start=1):
        lines.append(
            f"`{index}.` [{track.title}]({track.url}) — `{track.pretty_duration}`"
        )
    await status.edit_text(
        "\n".join(lines),
        reply_markup=search_keyboard(token, len(tracks)),
        disable_web_page_preview=True,
    )


@bot.on_message(
    filters.command(["playlist", "pl"], prefixes=config.COMMAND_PREFIXES)
    & filters.group
)
async def playlist_handler(client, message: Message) -> None:
    if not message.from_user or not await is_admin(
        message.chat.id, message.from_user.id
    ):
        await message.reply_text("⛔ Sirf group admins music control kar sakte hain.")
        return

    url = " ".join(message.command[1:]).strip()
    if not url:
        await message.reply_text(
            f"Usage: `{config.COMMAND_PREFIXES[0]}playlist <youtube playlist link>`"
        )
        return

    status = await message.reply_text("📥 Playlist padh raha hoon…")
    tracks = await downloader.playlist(url, limit=config.PLAYLIST_LIMIT)
    if not tracks:
        await status.edit_text("❌ Playlist khali hai ya link galat hai.")
        return

    chat_id = message.chat.id
    queue = get_queue(chat_id)
    for track in tracks:
        track.requested_by = _requested_by(message)
        track.requested_by_id = message.from_user.id

    if queue.stream_active or queue.current:
        queue.add_many(tracks)
        await status.edit_text(
            f"➕ **{len(tracks)} tracks queue me add kiye.**\n"
            f"📜 Queue length: `{len(queue.tracks)}`"
        )
        return

    first, rest = tracks[0], tracks[1:]
    queue.add_many(rest)
    try:
        await player.play_track(chat_id, first)
    except Exception as exc:  # noqa: BLE001
        await status.edit_text(f"❌ Voice chat join nahi kar paya: `{exc}`")
        return

    await status.edit_text(
        track_caption(first, "🎶 **Now playing** (playlist)"),
        reply_markup=player_keyboard(),
        disable_web_page_preview=True,
    )
