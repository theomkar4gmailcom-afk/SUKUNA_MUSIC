"""Pyrogram clients + the PyTgCalls instance (imported everywhere)."""

from __future__ import annotations

from pyrogram import Client
from pytgcalls import PyTgCalls

import config

# Controller bot: users send /play, /pause ... to this one.
bot = Client(
    name="stranger-music-bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="app.plugins"),
    in_memory=True,
)

# ASSISTANT account (string session). This is the account that actually joins
# the group voice chat, so add it to the group before using /play.
assistant = Client(
    name="stranger-music-assistant",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION_STRING,
    in_memory=True,
)

# Voice-chat engine bound to the assistant account.
call = PyTgCalls(assistant)
