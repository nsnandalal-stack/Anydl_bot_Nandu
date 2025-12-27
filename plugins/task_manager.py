from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time
import os
import aiohttp
import asyncio
import aria2p
import math
from helper_funcs.display import progress_for_pyrogram, humanbytes, time_formatter
from helper_funcs.ffmpeg import take_screen_shot, get_metadata, generate_screenshots
from plugins.command import USER_THUMBS

# --- MEMORY ---
TASKS = {}
USER_PREFS = {}
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

# --- HELPER: Find largest file ---
def find_largest_file(path):
    if os.path.isfile(path): return path
    largest_file = None
    largest_size = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            if file_size > largest_size:
                largest_size = file_size
                largest_file = file_path
    return largest_file

# --- 1. ENTRY POINT ---
@Client.on_message(filters.private & (filters.regex(r'^http') | filters.regex(r'^magnet') | filters.document))
async def incoming_task(client, message):
    user_id = message.from_user.id
    
    # Handle Rename Input
    if user_id in TASKS and TASKS[user_id].get("state") == "waiting_for_name":
        TASKS[user_id]["custom_name"] = message.text.strip()
        TASKS[user_id]["state"] = "menu"
        await message.delete()
        await show_dashboard(client, TASKS[user_id]["chat_id"], TASKS[user_id]["message_id"], user_id)
        return

    # Process New Link/File
    url = None
    is_torrent = False
    
    if message.document:
        if message.document.file_name.endswith(".torrent"):
            is_torrent = True
            file_path = await message.download()
            url = file_path
        else: return # Ignore other documents
    else:
        url = message.text.strip()
        if url.startswith("magnet"): is_torrent = True

    custom_name = None
    if url and "|" in url and not os.path.isfile(url):
        url, custom_name = url.split("|")
        url = url.strip()
        custom_name = custom_name.strip()

    # Default to user's last preference (or 'video')
    current_mode = USER_PREFS.get(user_id, "video")

    TASKS[user_id] = {
        "url": url, "is_torrent": is_torrent, "custom_name": custom_name,
        "mode": current_mode, "state": "menu", "chat_id": message.chat.id, "message_id": None
    }

    sent_msg = await message.reply_text("🔄 **Loading Dashboard...**", quote=True)
    TASKS[user_id]["message_id"] = sent_msg.id
    await show_dashboard(client, message.chat.id, sent_msg.id, user_id)


# --- 2. DASHBOARD ---
async def show_dashboard(client, chat_id, message_id, user_id):
    if user_id not in TASKS: return

    task = TASKS[user_id]
    
    # UI Logic
    if task["mode"] == "video":
        mode_text = "🎥 Mode: Streamable"
        mode_btn = "📂 Switch to File"
    else:
        mode_text = "📂 Mode: Normal File"
        mode_btn = "🎥 Switch to Video"

    name_display = task["custom_name"] if task["custom_name"] else "Default"
    type_display = "🧲 Torrent" if task["is_torrent"] else "🔗 Direct Link"

    text = (
        f"⚙️ **Task Dashboard**\n\n"
        f"**Source:** {type_display}\n"
        f"**Name:** `{name_display}`\n"
        f"**Current:** {mode_text}\n\n"
        f"👇 **Configure:**"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(mode_btn, callback_data="toggle_mode"),
         InlineKeyboardButton("✏️ Rename", callback_data="ask_rename")],
        [InlineKeyboardButton("▶️ Start Upload", callback_data="start_process"),
         InlineKeyboardButton("❌ Cancel", callback_data="cancel_task")]
    ])
    
    try:
        await client.edit_message_text(chat_id, message_id, text, reply_markup=buttons)
    except:
        pass # Ignore if text didn't change


# --- 3. BUTTON HANDLER ---
@Client.on_callback_query()
async def handle_buttons(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    # 1. Global Cancel
    if data == "cancel": 
        await query.message.edit("❌ Process Cancelled.")
        return

    # 2. Check Task Existence
    if user_id not in TASKS:
        await query.answer("❌ Task expired. Please send link again.", show_alert=True)
        return

    # 3. Toggle Mode (Video <-> File)
    if data == "toggle_mode":
        new_mode = "document" if TASKS[user_id]["mode"] == "video" else "video"
        TASKS[user_id]["mode"] = new_mode
        USER_PREFS[user_id] = new_mode # Save preference
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)
        await query.answer("Mode Switched!") # Feedback

    # 4. Ask Rename
    elif data == "ask_rename":
        TASKS[user_id]["state"] = "waiting_for_name"
        await query.message.edit(
            "📝 **Send me the new name now.**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]])
        )

    # 5. Back to Menu
    elif data == "back_to_menu":
        TASKS[user_id]["state"] = "menu"
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)

    # 6. Cancel Task
    elif data == "cancel_task":
        del TASKS[user_id]
        await query.message.edit("❌ Task Cancelled.")

    # 7. Start Process
    elif data == "start_process":
        await query.message.edit("🚀 **Starting Task...**")
        await process_task(client, query.message, user_id)


# --- 4. PROCESSOR ---
async def process_task(client, status_msg, user_id):
    task = TASKS[user_id]
    url, custom_name, mode, is_torrent = task["url"], task["custom_name"], task["mode"], task["is_torrent"]
    download_path, start_time = "downloads/", time.time()
    if not os.path.exists(download_path): os.makedirs(download_path)
    final_file_path = None
    gid = None

    try:
        # --- A. DOWNLOAD ---
        if is_torrent:
            if os.path.isfile(url): download = aria2.add_torrent(url); os.remove(url)
            else: download = aria2.add_magnet(url)
            gid = download.gid
            
            while not download.is_complete:
                download.update()
                if download.status == 'error': await status_msg.edit("❌ Torrent Error."); return
                if download.total_length > 0:
                     p = download.completed_length * 100 / download.total_length
                     try:
                        await status_msg.edit(
                            f"⬇️ **Downloading Torrent...**\n"
                            f"📦 **Size:** {humanbytes(download.completed_length)} / {humanbytes(download.total_length)}\n"
                            f"🚀 **Speed:** {humanbytes(download.download_speed)}/s\n"
                            f"⏳ **Progress:** {round(p, 2)}%",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
                        )
                     except: pass
                await asyncio.sleep(4)
            
            # Find Largest File Logic
            root_path = str(download.files[0].path)
            if not os.path.exists(root_path):
                possible_folder = os.path.join("downloads", download.name)
                if os.path.exists(possible_folder): root_path = possible_folder
            final_file_path = find_largest_file(root_path)
            if not final_file_path: final_file_path = find_largest_file("downloads/")
            
        else:
            # Direct Link
            filename = custom_name if custom_name else url.split("/")[-1]
            final_file_path = os.path.join(download_path, filename)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200: await status_msg.edit("❌ HTTP Error."); return
                    total_size = int(resp.headers.get('content-length', 0))
                    downloaded = 0
                    with open(final_file_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024*1024)
                            if not chunk: break
                            f.write(chunk)
                            downloaded += len(chunk)
                            now = time.time()
                            diff = now - start_time
                            if diff > 1 and (round(diff % 5.00) == 0 or downloaded == total_size):
                                speed = downloaded / diff if diff > 0 else 0
                                eta = (total_size - downloaded) / speed if speed > 0 else 0
                                try:
                                    await status_msg.edit(
                                        f"⬇️ **Downloading...**\n"
                                        f"📦 **Size:** {humanbytes(downloaded)} / {humanbytes(total_size)}\n"
                                        f"🚀 **Speed:** {humanbytes(speed)}/s\n"
                                        f"⏳ **ETA:** {time_formatter(eta*1000)}",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
                                    )
                                except: pass

        # --- B. RENAME & UPLOAD ---
        if custom_name:
            folder = os.path.dirname(final_file_path)
            new_path = os.path.join(folder, custom_name)
            try: os.rename(final_file_path, new_path); final_file_path = new_path
            except: pass
        
        filename = os.path.basename(final_file_path)
        await status_msg.edit("⚙️ **Processing Media...**")
        thumb_path = USER_THUMBS.get(user_id) if user_id in USER_THUMBS else await take_screen_shot(final_file_path, download_path, 10)
        width, height, duration = await get_metadata(final_file_path)

        await status_msg.edit("📤 **Uploading...**")
        if mode == "video" and filename.lower().endswith(('.mkv', '.mp4', '.webm', '.avi')):
            await client.send_video(
                chat_id=status_msg.chat.id, video=final_file_path,
                caption=f"🎥 **{filename}**\n⏱️ **Duration:** `{duration}s`\n📦 **Size:** `{humanbytes(os.path.getsize(final_file_path))}`",
                thumb=thumb_path, width=width, height=height, duration=duration, supports_streaming=True,
                progress=progress_for_pyrogram, progress_args=("📤 **Uploading Video...**", status_msg, start_time),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
            )
            ss = await generate_screenshots(final_file_path, download_path, duration)
            if ss:
                await client.send_media_group(status_msg.chat.id, [filters.InputMediaPhoto(s) for s in ss])
                for s in ss: os.remove(s)
        else:
            await client.send_document(
                chat_id=status_msg.chat.id, document=final_file_path,
                caption=f"📂 **{filename}**\n📦 **Size:** `{humanbytes(os.path.getsize(final_file_path))}`",
                thumb=thumb_path, progress=progress_for_pyrogram,
                progress_args=("📤 **Uploading File...**", status_msg, start_time),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
            )

        await status_msg.delete()
        if os.path.exists(final_file_path): os.remove(final_file_path)
        if thumb_path and "thumbs/" not in thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)
        if gid: aria2.remove([gid])
        del TASKS[user_id]

    except Exception as e:
        await status_msg.edit(f"❌ **Error:** {e}")
        if user_id in TASKS: del TASKS[user_id]
