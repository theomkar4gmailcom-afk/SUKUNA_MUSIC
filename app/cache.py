"""Tiny in-memory cache for /search results (token -> tracks)."""

from __future__ import annotations

import secrets
from typing import Dict, List

from app.queue import Track

RESULTS: Dict[str, List[Track]] = {}
MAX_ENTRIES = 50


def store(tracks: List[Track]) -> str:
    token = secrets.token_urlsafe(6)
    if len(RESULTS) > MAX_ENTRIES:
        RESULTS.pop(next(iter(RESULTS)), None)
    RESULTS[token] = tracks
    return token


def get(token: str) -> List[Track] | None:
    return RESULTS.get(token)


def pop(token: str) -> None:
    RESULTS.pop(token, None)
