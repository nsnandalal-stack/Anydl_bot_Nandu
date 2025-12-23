# ANYDL – Owner-Only Torrent Bot

A **private Telegram downloader bot** built with **Pyrogram v2**, designed for **personal use only**.  
Supports **`.torrent` file uploads**, strict limits, and **owner-only access**.

> ⚠️ This bot is NOT public  
> ⚠️ Only whitelisted owner IDs can use it  
> ⚠️ Torrent usage on Heroku is risky (see notes below)

---

## 🚀 One-Click Deploy (Heroku)

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](
https://www.heroku.com/deploy?template=https://github.com/nsnandalal/Anydl_bot_Nandu



> Heroku will read `app.json` and prompt you for required environment variables.

---

## ✅ Features

- 🔐 **Owner-only access** (via `OWNER_IDS` env var)
- 🧲 **Torrent support via `.torrent` files only**
- 📦 **Hard 4 GB download cap**
- 📊 `/status` – check active torrent progress
- 🛑 `/stop` – immediately stop active torrent
- 🧹 Auto-cleanup after 6 hours
- 🐳 **Docker-based deployment**
- 📉 Minimal logs (cloud-safe)

---

## ❌ Not Supported (by design)

- Magnet links
- Public users
- Inline buttons / UI menus
- Multi-user queues
- Forced channel join
- Guaranteed torrent completion

These are intentionally excluded to reduce abuse and platform risk.

---

## 📁 Project Structure

anydl-owner-only/
├── bot.py
├── config.py
├── auth.py
├── cleanup.py
├── requirements.txt
├── Dockerfile
├── Procfile
├── app.json
├── README.md
└── plugins/
├── torrent_file.py
├── status.py
└── stop.py


---

## ⚙️ Required Environment Variables

Heroku will ask for these during deploy (or add later in **Settings → Config Vars**):

| Variable | Description |
|--------|-------------|
| `API_ID` | Telegram API ID |
| `API_HASH` | Telegram API Hash |
| `BOT_TOKEN` | Telegram Bot Token |
| `OWNER_IDS` | Comma-separated Telegram user IDs (e.g. `519459195`) |

📌 Get API credentials: https://my.telegram.org  
📌 Get bot token from **@BotFather**

---

## 🤖 Bot Commands (Owner Only)

| Command | Description |
|------|-------------|
| `/start` | Bot health check |
| `/status` | Show torrent progress |
| `/stop` | Stop active torrent |
| Upload `.torrent` | Start torrent download |

---

## ⚠️ Important Heroku Warning (Read This)

Heroku **does NOT allow BitTorrent / P2P traffic** under its Acceptable Use Policy.

What this means:
- ❌ High chance of app suspension if torrents are used
- ❌ Owner-only access does NOT reduce this risk
- ✔️ HTTP / non-P2P features are generally safe

### Recommendation
- Use **Railway** for torrents (best-effort)
- Use **Heroku** only if you **disable torrent usage**

Your code is correct; any suspension would be **platform policy**, not a bug.

---

## 🐳 Docker Notes

- The file must be named **exactly** `Dockerfile`
- No file extension (`.py`, `.txt`, etc.)
- Heroku uses the Dockerfile because `stack: container` is set

---

## 🛑 Legal & Policy Notice

This project is for **personal use only**.

You are responsible for:
- Content you download
- Compliance with hosting provider policies
- Compliance with local laws

The author assumes **no liability** for misuse.

---

## 🧠 Final Notes

✔️ Clean architecture  
✔️ Owner-only enforced at startup  
✔️ Ready for Heroku & Railway  
⚠️ Torrent reliability depends on platform rules  

If you want a **Heroku-safe mode** (auto-disable torrents via env var), it can be added cleanly.
