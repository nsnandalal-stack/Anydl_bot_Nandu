import asyncio
import subprocess
import time
from pathlib import Path
from pyrogram import filters
from auth import owner_only
from config import DOWNLOAD_DIR, MAX_FILE_SIZE, TORRENT_STATE

@filters.private & owner_only() & filters.document
async def torrent_file_handler(_, message):
    if not message.document.file_name.endswith(".torrent"):
        return

    if TORRENT_STATE["active"]:
        await message.reply_text("⚠️ Torrent already running. Use /stop first.")
        return

    work_dir = DOWNLOAD_DIR / f"torrent_{message.id}"
    work_dir.mkdir(exist_ok=True)

    torrent_path = await message.download(file_name=work_dir / message.document.file_name)

    proc = subprocess.Popen(
        ["aria2c", "--file-allocation=none", "--dir", str(work_dir), torrent_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    TORRENT_STATE.update({
        "active": True,
        "process": proc,
        "start_time": time.time(),
        "path": work_dir,
        "downloaded_bytes": 0,
    })

    await message.reply_text("⏳ Torrent started.")

    try:
        while proc.poll() is None:
            await asyncio.sleep(5)
            size = sum(f.stat().st_size for f in work_dir.rglob("*") if f.is_file())
            TORRENT_STATE["downloaded_bytes"] = size
            if size > MAX_FILE_SIZE:
                proc.kill()
                await message.reply_text("❌ Stopped: exceeded 4 GB limit.")
                break
    finally:
        TORRENT_STATE.update({"active": False, "process": None})
