from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
import time
import os
import aiohttp
from helper_funcs.display import progress_for_pyrogram

@Client.on_message(filters.private & (filters.regex(r'^http') | filters.regex(r'^https')))
async def download_handler(client, message):
    url = message.text.strip()
    
    # 1. Check for Rename (Link | NewName.mp4)
    custom_name = None
    if "|" in url:
        url, custom_name = url.split("|")
        url = url.strip()
        custom_name = custom_name.strip()

    status_msg = await message.reply_text("🔎 Processing...", quote=True)
    start_time = time.time()

    download_path = "downloads/"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    try:
        # 2. Determine Filename
        filename = custom_name if custom_name else url.split("/")[-1]
        file_path = os.path.join(download_path, filename)

        await status_msg.edit(f"⬇️ Downloading: `{filename}`")
        
        # 3. Download
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024*1024)
                            if not chunk: break
                            f.write(chunk)
                else:
                    await status_msg.edit("❌ Error: Could not connect to link.")
                    return

        # 4. Upload with Progress & Buttons
        await status_msg.edit("📤 Uploading...")
        
        await client.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption=f"**File:** `{filename}`",
            progress=progress_for_pyrogram,
            progress_args=("📤 Uploading...", status_msg, start_time),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Rename 📝", callback_data="rename_help")],
                [InlineKeyboardButton("Cancel ❌", callback_data="cancel")]
            ])
        )
        
        await status_msg.delete()
        os.remove(file_path)

    except MessageNotModified:
        pass # <--- This prevents the crash!
    except Exception as e:
        await status_msg.edit(f"❌ Error: {e}")
