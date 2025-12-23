import asyncio, subprocess, time, re
from pathlib import Path
from pyrogram import filters
from auth import owner_only
from config import DOWNLOAD_DIR, MAX_FILE_SIZE, TORRENT_STATE

MAGNET = re.compile(r"^magnet:\?xt=urn:btih:", re.I)

@filters.private & owner_only()
async def torrent_handler(_, message):
    text = message.text or ""
    is_magnet = MAGNET.match(text)
    is_torrent = message.document and message.document.file_name.endswith(".torrent")

    if not is_magnet and not is_torrent:
        return

    if TORRENT_STATE["active"]:
        await message.reply_text("⚠️ A torrent is already running. Use /stop first.")
        return

    tdir = DOWNLOAD_DIR / f"torrent_{message.id}"
    tdir.mkdir(exist_ok=True)

    src = text
    if is_torrent:
        src = await message.download(file_name=tdir / message.document.file_name)

    proc = subprocess.Popen(
        ["aria2c", "--dir", str(tdir), src],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    TORRENT_STATE.update({
        "active": True,
        "process": proc,
        "start_time": time.time(),
        "path": tdir,
        "downloaded_bytes": 0
    })

    await message.reply_text("⏳ Torrent started.")

    try:
        while proc.poll() is None:
            await asyncio.sleep(5)
            size = sum(f.stat().st_size for f in tdir.rglob("*") if f.is_file())
            TORRENT_STATE["downloaded_bytes"] = size
            if size > MAX_FILE_SIZE:
                proc.kill()
                await message.reply_text("❌ Stopped: exceeded 4 GB limit.")
                break
    finally:
        TORRENT_STATE.update({"active": False, "process": None})
