import time
from pyrogram import filters
from auth import owner_only
from config import TORRENT_STATE, MAX_FILE_SIZE

@filters.private & owner_only() & filters.command("status")
async def status(_, message):
    if not TORRENT_STATE["active"]:
        await message.reply_text("ℹ️ No active torrent.")
        return

    used = TORRENT_STATE["downloaded_bytes"]
    elapsed = int(time.time() - TORRENT_STATE["start_time"])
    pct = (used / MAX_FILE_SIZE) * 100

    await message.reply_text(
        f"📊 Torrent Status\n\n"
        f"Downloaded: {used/1024**2:.1f} MB\n"
        f"Usage: {pct:.1f}% of 4 GB\n"
        f"Elapsed: {elapsed//60}m {elapsed%60}s"
    )
