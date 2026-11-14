# 🎵 Stranger Music — Telegram VC Music Bot

Telegram group ke **voice chat** me gaane / videos play karne wala bot.
Stack: **Python 3.11+**, **PyrogramMod**, **PyTgCalls 3.x** (NTgCalls), **yt-dlp**, **FFmpeg**.

> Yeh `@STRANGER_X_MUSIC_BOT` ka original code nahi hai (woh private hai) —
> yeh ek clean, self-hosted implementation hai jo wahi kaam karta hai.

---

## 1. Requirements

- Python 3.11 / 3.12
- `ffmpeg` (system package)
- Telegram `API_ID` + `API_HASH` → https://my.telegram.org/apps
- Bot token → [@BotFather](https://t.me/BotFather)
- Ek **assistant account** (normal Telegram account) jo voice chat join karega

---

## 2. Setup (local)

```bash
git clone <your-repo>   # ya files copy karo
cd stranger-music-bot

python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
sudo apt install ffmpeg                               # macOS: brew install ffmpeg

cp .env.example .env                                 # phir .env edit karo
python generate_session.py                           # SESSION_STRING yahan se
python main.py
```

`✅ ... is up` message aane par bot live hai.

---

## 3. Use

1. Bot ko apne group me add karo.
2. Assistant account ko bhi usi group me add karo (warna VC join nahi hoga).
3. Group me **voice chat start** karo.
4. `/play kesariya` bhejo — bas.

### Commands

| Command | Kaam |
|---|---|
| `/play <name/link>` | best match play / queue me add |
| `/vplay <name/link>` | video ke saath play |
| `/playlist <link>` | playlist queue me (`PLAYLIST_LIMIT` tak) |
| `/search <name>` | top results + inline buttons |
| `/play` (file ko reply) | Telegram audio/video file play |
| `/pause` `/resume` | pause / resume |
| `/skip` | next track |
| `/end` | stop + clear + VC leave |
| `/loop` | current track repeat |
| `/volume 1-200` | playback volume |
| `/queue` `/current` | queue / now-playing info |
| `/id` | chat & user id |
| `/stats` | sudoers only |

Admins-only by default (group admins, ya `SUDOERS` me listed ids).

---

## 4. Deploy

### Docker (recommended VPS)
```bash
cp .env.example .env   # fill it
docker compose up -d --build
docker compose logs -f
```

### Railway / Render / Koyeb / Heroku
- Repo push karo, Python buildpack use karo.
- Procfile: `worker: python main.py`
- Env vars `.env` jaisa hi set karo.
- Free tiers par yt-dlp datacenter IP block kar sakta hai → `PROXY_URL` ya `COOKIES_FILE` use karo.

---

## 5. Project structure

```
stranger-music-bot/
├── main.py                  # entry point + stream-end auto next
├── config.py                # env config + validation
├── generate_session.py      # assistant string session
├── requirements.txt
├── .env.example
├── Dockerfile / docker-compose.yml
└── app/
    ├── clients.py           # bot + assistant + PyTgCalls
    ├── queue.py             # Track / ChatQueue / QUEUES
    ├── downloader.py        # yt-dlp search, playlist, download
    ├── player.py            # MediaStream build, play/pause/skip/stop
    ├── utils.py             # admin check, keyboards, captions
    ├── cache.py             # /search result tokens
    └── plugins/
        ├── start.py         # /start /help /id
        ├── play.py          # /play /vplay /playlist /search
        ├── controls.py      # /pause /resume /skip /end /loop /volume
        ├── panel.py         # /queue /current
        ├── callbacks.py     # inline buttons
        └── sudo.py          # /stats
```

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `Voice chat join nahi kar paya` | VC start nahi hai, ya assistant group member nahi hai |
| `NoAudioSourceFound` / stream error | `ffmpeg` installed? `yt-dlp -U` se update karo |
| `Sign in as a bot is not allowed` | `SESSION_STRING` bot token se nahi, **user account** se banao |
| Video play nahi hota | `/vplay` use karo, aur `VIDEO_QUALITY` set karo |
| "Sign in to confirm you're not a bot" | `COOKIES_FILE=./cookies.txt` ya `PROXY_URL` |
| Pehli baar me bot mute lagta hai | Assistant ko group me admin banao (Manage Voice Chats) |

---

## 7. Legal

Sirf wahi content play karo jiska aapko haq hai. YouTube ko download/streaming
karte waqt unke Terms of Service ka khayal rakho — public bot chalane ki
zimmedari aapki hai.
