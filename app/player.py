"""Thin wrapper around PyTgCalls: start / stop / navigate the stream."""

from __future__ import annotations

from pathlib import Path

from pytgcalls.types import AudioQuality, MediaStream, VideoQuality

import config
from app.clients import call
from app.queue import Track, get_queue

AUDIO_QUALITIES = {
    "LOW": AudioQuality.LOW,
    "MEDIUM": AudioQuality.MEDIUM,
    "HIGH": AudioQuality.HIGH,
    "STUDIO": AudioQuality.STUDIO,
}

VIDEO_QUALITIES = {
    "SD_360p": VideoQuality.SD_360p,
    "SD_480p": VideoQuality.SD_480p,
    "HD_720p": VideoQuality.HD_720p,
    "FHD_1080p": VideoQuality.FHD_1080p,
    "QHD_2K": VideoQuality.QHD_2K,
    "UHD_4K": VideoQuality.UHD_4K,
}


def build_stream(track: Track) -> MediaStream:
    """Turn a Track into a PyTgCalls MediaStream."""
    audio = AUDIO_QUALITIES.get(config.AUDIO_QUALITY, AudioQuality.HIGH)
    source = str(track.url)

    if track.is_video:
        video = VIDEO_QUALITIES.get(config.VIDEO_QUALITY, VideoQuality.HD_720p)
        return MediaStream(
            source,
            audio_parameters=audio,
            video_parameters=video,
            ffmpeg_parameters="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        )

    # Audio only: explicitly ignore the video track.
    return MediaStream(
        source,
        audio_parameters=audio,
        video_flags=MediaStream.Flags.IGNORE,
        ffmpeg_parameters="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    )


async def play_track(chat_id: int, track: Track) -> None:
    """Start streaming a track in the chat's voice chat and update state."""
    queue = get_queue(chat_id)
    queue.current = track
    queue.paused = False
    queue.stream_active = True
    await call.play(chat_id, build_stream(track))


async def play_next(chat_id: int) -> Track | None:
    """Play the next queued track. Returns it, or None if the queue is empty."""
    queue = get_queue(chat_id)
    next_track = queue.pop_next()
    if not next_track:
        await stop_stream(chat_id)
        return None
    await play_track(chat_id, next_track)
    return next_track


async def stop_stream(chat_id: int) -> None:
    """Leave the voice chat and wipe the queue."""
    queue = get_queue(chat_id)
    queue.clear()
    queue.current = None
    try:
        await call.leave_call(chat_id, close=True)
    except Exception:  # already left / never joined
        pass


async def pause_stream(chat_id: int) -> bool:
    queue = get_queue(chat_id)
    ok = await call.pause(chat_id)
    if ok:
        queue.paused = True
    return ok


async def resume_stream(chat_id: int) -> bool:
    queue = get_queue(chat_id)
    ok = await call.resume(chat_id)
    if ok:
        queue.paused = False
    return ok


async def set_volume(chat_id: int, volume: int) -> None:
    await call.change_volume_call(chat_id, max(1, min(200, volume)))


async def played_time(chat_id: int):
    try:
        return await call.time(chat_id)
    except Exception:  # no active stream
        return None


def cleanup_file(path: str | Path) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
