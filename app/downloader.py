"""YouTube search / metadata helpers built on yt-dlp (async-safe wrappers)."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

import yt_dlp

import config
from app.queue import Track

URL_RE = re.compile(r"^(https?://|www\.)", re.IGNORECASE)


def _base_opts() -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "extract_flat": False,
        "socket_timeout": 20,
        "retries": 3,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "default_search": "ytsearch",
    }
    if config.COOKIES_FILE and Path(config.COOKIES_FILE).exists():
        opts["cookiefile"] = config.COOKIES_FILE
    if config.PROXY_URL:
        opts["proxy"] = config.PROXY_URL
    return opts


def _to_track(entry: dict | None, is_video: bool) -> Track | None:
    if not entry:
        return None
    video_id = str(entry.get("id") or "")
    url = entry.get("webpage_url") or entry.get("url") or ""
    if url and not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={video_id}"
    if not url:
        return None
    thumbnails = entry.get("thumbnails") or []
    thumbnail = entry.get("thumbnail") or (
        thumbnails[-1].get("url") if thumbnails else None
    )
    return Track(
        title=(entry.get("title") or "Unknown title").strip(),
        url=url,
        duration=int(entry.get("duration") or 0),
        thumbnail=thumbnail,
        is_video=is_video,
        video_id=video_id,
    )


def _search_blocking(query: str, limit: int, is_video: bool) -> list[Track]:
    opts = _base_opts()
    if URL_RE.match(query):
        target = query
    else:
        target = f"ytsearch{limit}:{query}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(target, download=False)
    if not info:
        return []
    if info.get("_type") == "playlist":
        entries = info.get("entries") or []
        tracks = [_to_track(e, is_video) for e in list(entries)[:limit]]
        return [t for t in tracks if t]
    track = _to_track(info, is_video)
    return [track] if track else []


def _playlist_blocking(url: str, limit: int, is_video: bool) -> list[Track]:
    opts = _base_opts()
    opts.update({"noplaylist": False, "extract_flat": "in_playlist"})
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        return []
    entries = info.get("entries") or []
    tracks: list[Track] = []
    for entry in entries:
        if len(tracks) >= limit:
            break
        track = _to_track(entry, is_video)
        if track:
            tracks.append(track)
    return tracks


async def search(query: str, limit: int | None = None, is_video: bool = False) -> list[Track]:
    """Search YouTube (or resolve a direct URL) without downloading."""
    limit = limit or config.SEARCH_LIMIT
    try:
        return await asyncio.to_thread(_search_blocking, query, limit, is_video)
    except Exception:  # noqa: BLE001 - yt-dlp raises many types
        return []


async def playlist(url: str, limit: int | None = None, is_video: bool = False) -> list[Track]:
    limit = limit or config.PLAYLIST_LIMIT
    try:
        return await asyncio.to_thread(_playlist_blocking, url, limit, is_video)
    except Exception:  # noqa: BLE001
        return []


def _download_blocking(url: str, is_video: bool) -> str | None:
    outtmpl = str(config.DOWNLOAD_DIR / "%(id)s.%(ext)s")
    fmt = "bv*[height<=720]+ba/b[height<=720]/b" if is_video else "bestaudio/best"
    opts = {
        **_base_opts(),
        "skip_download": False,
        "noplaylist": True,
        "format": fmt,
        "outtmpl": outtmpl,
        "restrictfilenames": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            return None
        path = ydl.prepare_filename(info)
    if Path(path).exists():
        return path
    # merged outputs change extension (webm/m4a/mp4)
    for candidate in config.DOWNLOAD_DIR.glob(f"{info.get('id')}.*"):
        return str(candidate)
    return None


async def download(url: str, is_video: bool = False) -> str | None:
    """Download a track to disk (used for Telegram audio/video files)."""
    return await asyncio.to_thread(_download_blocking, url, is_video)
