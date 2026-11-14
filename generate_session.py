"""
Generate a Pyrogram string session for the ASSISTANT account.

    python generate_session.py

Login with a normal Telegram account (not the bot). That account will be the
one joining voice chats, so it must be a member of your group.
"""

from pyrogram import Client

print(
    "\n=== Stranger Music — assistant session generator ===\n"
    "Telegram API details: https://my.telegram.org/apps\n"
)

api_id = int(input("API_ID: ").strip())
api_hash = input("API_HASH: ").strip()

with Client(
    name="assistant_session",
    api_id=api_id,
    api_hash=api_hash,
    in_memory=True,
) as app:
    print("\nYour SESSION_STRING (keep it secret!):\n")
    print(app.export_session_string())
    print("\nPaste it in .env as SESSION_STRING=...\n")
