"""
Central configuration. Everything is read from environment variables
(see .env.example) so you never have to edit this file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _get_int(name: str, default: int | None = None) -> int | None:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _get_list(name: str) -> list[int]:
    raw = os.getenv(name, "")
    items: list[int] = []
    for chunk in raw.replace(",", " ").split():
        try:
            items.append(int(chunk))
        except ValueError:
            pass
    return items


# ---------------------------------------------------------------- Telegram API
API_ID: int = _get_int("API_ID", 0)
API_HASH: str = os.getenv("API_HASH", "")

# Bot token from @BotFather (the "controller" bot users talk to)
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Pyrogram string session of the ASSISTANT account (the account that joins
# the voice chat and streams the audio). Generate it with: python generate_session.py
SESSION_STRING: str = os.getenv("SESSION_STRING", "")

# ---------------------------------------------------------------- Behaviour
COMMAND_PREFIXES: list[str] = list(os.getenv("COMMAND_PREFIXES", "/!."))
SUDOERS: list[int] = _get_list("SUDOERS")

# Audio / video quality passed to PyTgCalls: HIGH | MEDIUM | LOW | STUDIO
AUDIO_QUALITY: str = os.getenv("AUDIO_QUALITY", "HIGH").upper()
VIDEO_QUALITY: str = os.getenv("VIDEO_QUALITY", "HD_720p")

# Max tracks a single /playlist may add at once
PLAYLIST_LIMIT: int = _get_int("PLAYLIST_LIMIT", 20)
# How many YouTube results /search shows
SEARCH_LIMIT: int = _get_int("SEARCH_LIMIT", 5)

# Optional extras -------------------------------------------------------
COOKIES_FILE: str = os.getenv("COOKIES_FILE", "")        # for age-restricted videos
PROXY_URL: str = os.getenv("PROXY_URL", "")              # e.g. socks5://host:port
DOWNLOAD_DIR: Path = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

LOG_CHANNEL: int = _get_int("LOG_CHANNEL", 0) or 0
SUPPORT_CHAT: str = os.getenv("SUPPORT_CHAT", "https://t.me/")
OWNER_USERNAME: str = os.getenv("OWNER_USERNAME", "")

BOT_NAME: str = os.getenv("BOT_NAME", "Stranger Music")
START_IMAGE: str = os.getenv("START_IMAGE", "")

# Inline keyboard / button links
BUTTON_ADD_GROUP: str = os.getenv("BUTTON_ADD_GROUP", "")
BUTTON_CHANNEL: str = os.getenv("BUTTON_CHANNEL", "")


def validate() -> None:
    """Fail fast with a readable message instead of a cryptic Pyrogram error."""
    missing = []
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not SESSION_STRING:
        missing.append("SESSION_STRING")
    if missing:
        raise SystemExit(
            "Missing required config: " + ", ".join(missing)
            + "\nCopy .env.example to .env and fill it in."
        )
