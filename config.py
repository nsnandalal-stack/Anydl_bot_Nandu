import os
from pathlib import Path

# ===============================
# 🔐 OWNER ACCESS CONTROL
# ===============================
OWNER_IDS = {
    int(uid.strip())
    for uid in os.environ.get("OWNER_IDS", "").split(",")
    if uid.strip().isdigit()
}

if not OWNER_IDS:
    raise RuntimeError(
        "OWNER_IDS is not set. "
        "Set OWNER_IDS as comma-separated Telegram user IDs."
    )

# ===============================
# 🤖 TELEGRAM CONFIG
# ===============================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError(
        "API_ID, API_HASH, and BOT_TOKEN must be set."
    )

# ===============================
# 📁 STORAGE
# ===============================
BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ===============================
# 📦 LIMITS
# ===============================
MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4 GB
FILE_TTL_HOURS = 6

# ===============================
# 🧠 TORRENT STATE
# ===============================
TORRENT_STATE = {
    "active": False,
    "process": None,
    "downloaded_bytes": 0,
    "start_time": None,
    "path": None,
}

# ===============================
# 📉 LOGGING
# ===============================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
