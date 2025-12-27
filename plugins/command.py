from pyrogram import Client, filters
import os

# --- 🔒 SECURITY SETTINGS ---
# We keep the current ID. If it's wrong, the bot will tell us why.
AUTH_USERS = [519459195] 

# Helper to check if user is allowed
def is_authorized(user_id):
    return user_id in AUTH_USERS

# Store user settings in memory
USER_THUMBS = {}

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    
    # 🔍 DEBUG MODE: This prints YOUR ID if access is denied
    if not is_authorized(user_id):
        await message.reply_text(
            f"⛔ **Access Denied**\n\n"
            f"The ID inside the code is: `{AUTH_USERS[0]}`\n"
            f"But YOUR ID is: `{user_id}`\n\n"
            f"👉 **FIX:** Copy `{user_id}` and paste it into plugins/command.py"
        )
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
        await message.reply_text(f"⚠️ Access Denied. Your ID: `{message.from_user.id}`")
        return

    if message.reply_to_message.photo:
        if not os.path.exists("thumbs"): os.makedirs("thumbs")
        path = await client.download_media(message.reply_to_message, file_name=f"thumbs/{message.from_user.id}.jpg")
        USER_THUMBS[message.from_user.id] = path
        await message.reply_text("✅ **Thumbnail Saved!** Future videos will use this cover.")
    else:
        await message.reply_text("❌ Reply to a photo to set it as thumbnail.")

@Client.on_message(filters.command("del_thumb"))
async def delete_thumbnail(client, message):
    if not is_authorized(message.from_user.id):
        await message.reply_text(f"⚠️ Access Denied. Your ID: `{message.from_user.id}`")
        return

    user_id = message.from_user.id
    if user_id in USER_THUMBS:
        if os.path.exists(USER_THUMBS[user_id]):
            os.remove(USER_THUMBS[user_id])
        del USER_THUMBS[user_id]
        await message.reply_text("🗑️ **Thumbnail Deleted.**")
    else:
        await message.reply_text("❌ You don't have a custom thumbnail set.")
