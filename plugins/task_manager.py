from pyrogram import Client, filters
import os

# --- 🔒 SECURITY SETTINGS ---
# 👇 PASTE YOUR ID HERE (Replace 123456789 with your real number)
AUTH_USERS = [123456789] 

# Helper to check if user is allowed
def is_authorized(user_id):
    return user_id in AUTH_USERS

# Store user settings in memory
USER_THUMBS = {}

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    # Check if user is the owner
    if not is_authorized(message.from_user.id):
        await message.reply_text("⚠️ **Access Denied.**\nYou are not authorized to use this bot.\nContact the owner: @poocha")
        return

    await message.reply_text(
        "👋 **Hello! I am your Private Pro Downloader.**\n\n"
        "**Features:**\n"
        "🎥 Streamable Videos\n"
        "🟥 YouTube Support\n"
        "🧲 Torrent & Magnet Support\n\n"
        "**Commands:**\n"
        "/set_thumb - Reply to an image to set custom thumbnail\n"
        "/del_thumb - Delete your custom thumbnail\n"
        "Just send a Link or Magnet to start!"
    )

@Client.on_message(filters.command("set_thumb") & filters.reply)
async def set_thumbnail(client, message):
    if not is_authorized(message.from_user.id):
        await message.reply_text("⚠️ Access Denied.")
        return

    if message.reply_to_message.photo:
        # Create folder if not exists
        if not os.path.exists("thumbs"): os.makedirs("thumbs")
        
        path = await client.download_media(message.reply_to_message, file_name=f"thumbs/{message.from_user.id}.jpg")
        USER_THUMBS[message.from_user.id] = path
        await message.reply_text("✅ **Thumbnail Saved!** Future videos will use this cover.")
    else:
        await message.reply_text("❌ Reply to a photo to set it as thumbnail.")

@Client.on_message(filters.command("del_thumb"))
async def delete_thumbnail(client, message):
    if not is_authorized(message.from_user.id):
        await message.reply_text("⚠️ Access Denied.")
        return

    user_id = message.from_user.id
    if user_id in USER_THUMBS:
        if os.path.exists(USER_THUMBS[user_id]):
            os.remove(USER_THUMBS[user_id])
        del USER_THUMBS[user_id]
        await message.reply_text("🗑️ **Thumbnail Deleted.**")
    else:
        await message.reply_text("❌ You don't have a custom thumbnail set.")
