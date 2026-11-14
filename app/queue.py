"""Per-chat playback queue."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Track:
    title: str
    url: str                      # playable page / stream url
    duration: int = 0             # seconds
    thumbnail: str | None = None
    requested_by: str = ""
    requested_by_id: int = 0
    is_video: bool = False
    video_id: str = ""

    @property
    def pretty_duration(self) -> str:
        return format_duration(self.duration)


@dataclass
class ChatQueue:
    tracks: list[Track] = field(default_factory=list)
    current: Track | None = None
    loop: bool = False            # True -> replay current track forever
    loop_all: bool = False        # True -> append finished track to the end
    paused: bool = False
    stream_active: bool = False

    # ------------------------------------------------------------- helpers
    @property
    def is_empty(self) -> bool:
        return not self.tracks

    def add(self, track: Track) -> None:
        self.tracks.append(track)

    def add_many(self, tracks: list[Track]) -> None:
        self.tracks.extend(tracks)

    def pop_next(self) -> Track | None:
        if not self.tracks:
            return None
        return self.tracks.pop(0)

    def clear(self) -> None:
        self.tracks.clear()
        self.current = None
        self.paused = False
        self.stream_active = False

    def total_duration(self) -> int:
        total = sum(t.duration or 0 for t in self.tracks)
        if self.current:
            total += self.current.duration or 0
        return total


QUEUES: dict[int, ChatQueue] = {}


def get_queue(chat_id: int) -> ChatQueue:
    if chat_id not in QUEUES:
        QUEUES[chat_id] = ChatQueue()
    return QUEUES[chat_id]


def format_duration(seconds: int | None) -> str:
    seconds = int(seconds or 0)
    if seconds <= 0:
        return "LIVE"
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def queue_text(chat_id: int) -> str:
    q = get_queue(chat_id)
    if not q.current and not q.tracks:
        return "Kuch bhi queue me nahi hai. /play <song> bhejo."

    lines = []
    if q.current:
        lines.append(
            "**Abhi chal raha hai:**\n"
            f"▶️ [{q.current.title}]({q.current.url}) — `{q.current.pretty_duration}`"
            f" (by {q.current.requested_by})"
        )
    if q.tracks:
        lines.append("\n**Queue:**")
        for index, track in enumerate(q.tracks[:15], start=1):
            lines.append(
                f"{index}. [{track.title}]({track.url}) — `{track.pretty_duration}`"
            )
        if len(q.tracks) > 15:
            lines.append(f"\n… aur {len(q.tracks) - 15} tracks")
    total = format_duration(q.total_duration())
    lines.append(f"\n**Total:** {total} • **Loop:** {'on' if q.loop else 'off'}")
    return "\n".join(lines)
