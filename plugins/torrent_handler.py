from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
import time
import os
import asyncio
import aria2p
from helper_funcs.display import progress_for_pyrogram, humanbytes

# Connect to the internal Torrent Engine (Aria2)
aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""
    )
)

@Client.on_message(filters.private & (filters.regex(r'^magnet') | filters.document))
async def torrent_handler(client, message):
    # 1. Handle Magnet Link or .torrent file
    if message.document:
        try:
            file_path = await message.download()
            download = aria2.add_torrent(file_path)
            os.remove(file_path)
        except Exception as e:
            await message.reply_text(f"❌ Error reading .torrent file: {e}")
            return
    else:
        magnet_link = message.text.strip()
        
        # Rename Logic: magnet... | NewName.mp4
        custom_name = None
        if "|" in magnet_link:
            magnet_link, custom_name = magnet_link.split("|")
            magnet_link = magnet_link.strip()
            custom_name = custom_name.strip()
            
        try:
            download = aria2.add_magnet(magnet_link)
        except Exception as e:
            await message.reply_text(f"❌ Error adding magnet: {e}")
            return

    status_msg = await message.reply_text("🧲 Added to Queue...", quote=True)
    start_time = time.time()
    
    # 2. Track Download Progress
    while not download.is_complete:
        try:
            download.update()
            if download.status == 'error':
                await status_msg.edit("❌ Torrent Download Failed.")
                return
            
            # Update Progress Bar
            if download.total_length > 0:
                current = download.completed_length
                total = download.total_length
                speed = download.download_speed
                percentage = current * 100 / total
                
                await status_msg.edit(
                    f"⬇️ **Downloading Torrent...**\n"
                    f"📦 **Size:** {humanbytes(current)} / {humanbytes(total)}\n"
                    f"🚀 **Speed:** {humanbytes(speed)}/s\n"
                    f"⏳ **Progress:** {round(percentage, 2)}%"
                )
        except MessageNotModified:
            pass # Ignore "duplicate message" error
        except Exception:
            pass
        
        await asyncio.sleep(4) # Refresh every 4 seconds

    # 3. Download Finished - Prepare Upload
    await status_msg.edit("✅ Download Finished! Processing...")
    
    try:
        # Find the file
        downloaded_file_path = str(download.files[0].path)
        
        # Apply Rename if requested
        if 'custom_name' in locals() and custom_name:
            new_path = os.path.join(os.path.dirname(downloaded_file_path), custom_name)
            os.rename(downloaded_file_path, new_path)
            downloaded_file_path = new_path
            filename = custom_name
        else:
            filename = os.path.basename(downloaded_file_path)

        # 4. Upload to Telegram
        await client.send_document(
            chat_id=message.chat.id,
            document=downloaded_file_path,
            caption=f"**File:** `{filename}`",
            progress=progress_for_pyrogram,
            progress_args=("📤 Uploading...", status_msg, start_time),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Rename 📝", callback_data="rename_help")],
                [InlineKeyboardButton("Cancel ❌", callback_data="cancel")]
            ])
        )
        
        # Cleanup
        await status_msg.delete()
        aria2.remove([download])
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)

    except Exception as e:
        await status_msg.edit(f"❌ Upload Error: {e}")
