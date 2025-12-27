from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time
import os
import aiohttp
import asyncio
import aria2p
import yt_dlp
from helper_funcs.display import progress_for_pyrogram, humanbytes, time_formatter
from helper_funcs.ffmpeg import take_screen_shot, get_metadata, generate_screenshots
from plugins.command import USER_THUMBS

# --- MEMORY ---
TASKS = {}
USER_PREFS = {}
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

# --- HELPER: YOUTUBE DOWNLOADER ---
def run_ytdlp(url, mode, output_path):
    # This runs inside a thread to prevent blocking the bot
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
    }
    
    if mode == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        })
    else:
        # Video Mode (Best Quality + Streamable format)
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Return the actual filename (sometimes yt-dlp changes ext)
        return ydl.prepare_filename(info).rsplit('.', 1)[0] + ('.mp3' if mode == 'audio' else '.mp4')

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

    # Process New Link
    url = None
    is_torrent = False
    is_youtube = False
    
    if message.document:
        if message.document.file_name.endswith(".torrent"):
            is_torrent = True
            file_path = await message.download()
            url = file_path
        else: return
    else:
        url = message.text.strip()
        if url.startswith("magnet"): is_torrent = True
        elif "youtube.com" in url or "youtu.be" in url: is_youtube = True

    custom_name = None
    if url and "|" in url and not os.path.isfile(url):
        url, custom_name = url.split("|")
        url = url.strip()
        custom_name = custom_name.strip()

    # Default Mode Logic
    # YouTube defaults to "video", others default to "video" (Streamable)
    current_mode = "video" 

    TASKS[user_id] = {
        "url": url, "is_torrent": is_torrent, "is_youtube": is_youtube,
        "custom_name": custom_name, "mode": current_mode,
        "state": "menu", "chat_id": message.chat.id, "message_id": None
    }

    sent_msg = await message.reply_text("🔄 **Analyzing Link...**", quote=True)
    TASKS[user_id]["message_id"] = sent_msg.id
    await show_dashboard(client, message.chat.id, sent_msg.id, user_id)


# --- 2. DASHBOARD ---
async def show_dashboard(client, chat_id, message_id, user_id):
    if user_id not in TASKS: return
    task = TASKS[user_id]
    
    # UI Logic
    name_display = task["custom_name"] if task["custom_name"] else "Default"
    
    if task["is_youtube"]:
        # --- YOUTUBE DASHBOARD ---
        type_display = "🟥 YouTube"
        if task["mode"] == "audio":
            mode_text = "🎵 Audio (MP3)"
            switch_btn = "🎬 Switch to Video"
        else:
            mode_text = "🎬 Video (MP4)"
            switch_btn = "🎵 Switch to Audio"
    else:
        # --- STANDARD DASHBOARD ---
        type_display = "🧲 Torrent" if task["is_torrent"] else "🔗 Direct Link"
        if task["mode"] == "video":
            mode_text = "🎥 Streamable Video"
            switch_btn = "📂 Switch to File"
        else:
            mode_text = "📂 Normal File"
            switch_btn = "🎥 Switch to Video"

    text = (
        f"⚙️ **Task Dashboard**\n\n"
        f"**Source:** {type_display}\n"
        f"**Name:** `{name_display}`\n"
        f"**Mode:** {mode_text}\n\n"
        f"👇 **Select Option:**"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(switch_btn, callback_data="toggle_mode"),
         InlineKeyboardButton("✏️ Rename", callback_data="ask_rename")],
        [InlineKeyboardButton("▶️ Start Download", callback_data="start_process"),
         InlineKeyboardButton("❌ Cancel", callback_data="cancel_task")]
    ])
    
    try: await client.edit_message_text(chat_id, message_id, text, reply_markup=buttons)
    except: pass


# --- 3. BUTTONS ---
@Client.on_callback_query()
async def handle_buttons(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    if data == "cancel": 
        await query.message.edit("❌ Cancelled."); return
    if user_id not in TASKS:
        await query.answer("❌ Expired.", show_alert=True); return

    # Toggle Logic (Switches between Video/Audio for YT, or Video/File for others)
    if data == "toggle_mode":
        current = TASKS[user_id]["mode"]
        if TASKS[user_id]["is_youtube"]:
            new_mode = "audio" if current == "video" else "video"
        else:
            new_mode = "document" if current == "video" else "video"
            
        TASKS[user_id]["mode"] = new_mode
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)

    elif data == "ask_rename":
        TASKS[user_id]["state"] = "waiting_for_name"
        await query.message.edit(
            "📝 **Send new name:**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]])
        )

    elif data == "back_to_menu":
        TASKS[user_id]["state"] = "menu"
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)

    elif data == "cancel_task":
        del TASKS[user_id]
        await query.message.edit("❌ Task Cancelled.")

    elif data == "start_process":
        await query.message.edit("🚀 **Starting...**")
        await process_task(client, query.message, user_id)


# --- 4. PROCESSOR ---
async def process_task(client, status_msg, user_id):
    task = TASKS[user_id]
    url, custom_name, mode = task["url"], task["custom_name"], task["mode"]
    download_path, start_time = "downloads/", time.time()
    if not os.path.exists(download_path): os.makedirs(download_path)
    final_file_path = None
    gid = None

    try:
        # --- A. DOWNLOAD PHASE ---
        if task["is_youtube"]:
            # YOUTUBE LOGIC
            await status_msg.edit(f"⬇️ **Downloading from YouTube...**\n(This may take time for processing)")
            try:
                # Run yt-dlp in a separate thread so it doesn't freeze the bot
                final_file_path = await asyncio.to_thread(run_ytdlp, url, mode, download_path)
            except Exception as e:
                await status_msg.edit(f"❌ YouTube Error: {e}")
                return

        elif task["is_torrent"]:
            # TORRENT LOGIC
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
                            f"⏳ **Progress:** {round(p, 2)}%",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
                        )
                     except: pass
                await asyncio.sleep(4)
            final_file_path = find_largest_file(str(download.files[0].path))
            if not final_file_path: final_file_path = find_largest_file("downloads/")

        else:
            # HTTP DIRECT LINK LOGIC
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
                            if time.time() - start_time > 4:
                                try: await status_msg.edit(f"⬇️ **Downloading:** {humanbytes(downloaded)} / {humanbytes(total_size)}")
                                except: pass

        # --- B. RENAME & UPLOAD ---
        if custom_name and not task["is_youtube"]:
            # Standard rename logic for non-YT files
            folder = os.path.dirname(final_file_path)
            new_path = os.path.join(folder, custom_name)
            try: os.rename(final_file_path, new_path); final_file_path = new_path
            except: pass
        
        filename = os.path.basename(final_file_path)
        await status_msg.edit("⚙️ **Processing...**")
        
        thumb_path = USER_THUMBS.get(user_id)
        if not thumb_path and mode == "video": 
             thumb_path = await take_screen_shot(final_file_path, download_path, 10)

        # Upload Logic
        await status_msg.edit("📤 **Uploading...**")
        
        if mode == "audio":
            # Audio Upload
            await client.send_audio(
                chat_id=status_msg.chat.id, audio=final_file_path,
                caption=f"🎵 **{filename}**", thumb=thumb_path,
                progress=progress_for_pyrogram, progress_args=("📤 **Uploading Audio...**", status_msg, start_time),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
            )
        elif mode == "video":
            # Video Upload
            width, height, duration = await get_metadata(final_file_path)
            await client.send_video(
                chat_id=status_msg.chat.id, video=final_file_path,
                caption=f"🎥 **{filename}**\n⏱️ **Duration:** `{duration}s`",
                thumb=thumb_path, width=width, height=height, duration=duration, supports_streaming=True,
                progress=progress_for_pyrogram, progress_args=("📤 **Uploading Video...**", status_msg, start_time),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
            )
        else:
            # Document Upload
            await client.send_document(
                chat_id=status_msg.chat.id, document=final_file_path,
                caption=f"📂 **{filename}**", thumb=thumb_path,
                progress=progress_for_pyrogram, progress_args=("📤 **Uploading File...**", status_msg, start_time),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
            )

        # Cleanup
        await status_msg.delete()
        if os.path.exists(final_file_path): os.remove(final_file_path)
        if thumb_path and "thumbs/" not in thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)
        if gid: aria2.remove([gid])
        del TASKS[user_id]

    except Exception as e:
        await status_msg.edit(f"❌ **Error:** {e}")
        if user_id in TASKS: del TASKS[user_id]
