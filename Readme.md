# ANYDL – Owner-Only Torrent Bot (Railway)

A **private Telegram downloader bot** built with **Pyrogram v2**, designed strictly for **personal use** and optimized for **Railway deployment using Docker**.

> ⚠️ This bot is NOT public  
> ⚠️ Only the owner can use it  
> ⚠️ Torrent support is best-effort due to Railway limitations

---

## 🚀 One-Click Deploy (Railway)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)


> After clicking the button, connect your GitHub repo when prompted.  
> Railway will auto-detect **Docker** and build automatically.

---

## ✅ Features

- 🔐 **Owner-only access** (hard enforced)
- 🧲 **Torrent & magnet support** via aria2
- 📦 **Hard 4 GB download cap**
- 📊 `/status` – monitor active torrent
- 🛑 `/stop` – kill active torrent immediately
- 🧹 Auto-delete downloads after 6 hours
- 🐳 **Docker-based deployment**
- 📉 Minimal logs (safe for cloud hosting)

---

## ❌ Not Supported (by design)

- Public users
- Inline buttons or UI menus
- Multi-user queues
- Forced channel join
- Guaranteed torrent completion

This is intentional to reduce abuse and platform risk.

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
├── torrent.py
├── status.py
└── stop.py


---

## 🚀 Deploy on Railway (Recommended)

### Step 1: Push to GitHub
Create a new GitHub repository and push this project.

---

### Step 2: Deploy on Railway
1. Go to https://railway.app
2. Click **New Project → Deploy from GitHub Repo**
3. Select your repository
4. Railway will **auto-detect Docker**
5. Click **Deploy**

No additional configuration required.

---

### Step 3: Set Environment Variables

In Railway → **Variables**, add:

| Variable | Description |
|--------|-------------|
| `API_ID` | Telegram API ID |
| `API_HASH` | Telegram API Hash |
| `BOT_TOKEN` | Telegram Bot Token |

📌 Get API ID & HASH: https://my.telegram.org  
📌 Get BOT_TOKEN from **@BotFather**

---

## 🤖 Bot Commands (Owner Only)

| Command | Description |
|------|-------------|
| `/start` | Bot health check |
| `/status` | Show torrent progress |
| `/stop` | Stop active torrent |
| Magnet / `.torrent` | Start torrent download |

---

## ⚠️ Railway Torrent Usage Warning

Railway does **not officially support P2P traffic**.

What this means in practice:
- Small, well-seeded torrents usually work
- Slow or large torrents may fail
- High bandwidth usage may trigger throttling
- Containers can restart without notice

### Recommended usage
- Prefer torrents under **2–3 GB**
- Use well-seeded public torrents
- Monitor progress with `/status`
- Stop early if progress is slow

Failures here are **platform-level**, not code bugs.

---

## 🐳 Docker Notes

- The file must be named **exactly** `Dockerfile`
- No file extension (`.py`, `.txt`, etc.)
- Railway builds automatically using Docker

---

## 🛑 Legal & Policy Notice

This bot is for **personal use only**.

You are responsible for:
- Content you download
- Compliance with Railway policies
- Compliance with local laws

The author assumes **no liability** for misuse.


