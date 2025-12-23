from pyrogram import filters
from auth import owner_only
from config import TORRENT_STATE

@filters.private & owner_only() & filters.command("stop")
async def stop(_, message):
    proc = TORRENT_STATE.get("process")
    if not proc or not TORRENT_STATE["active"]:
        await message.reply_text("ℹ️ No active torrent to stop.")
        return

    proc.kill()
    TORRENT_STATE.update({
        "active": False,
        "process": None,
        "downloaded_bytes": 0,
        "path": None
    })

    await message.reply_text("🛑 Torrent stopped.")
