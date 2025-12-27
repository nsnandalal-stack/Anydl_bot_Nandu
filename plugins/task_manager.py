from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import time
import os
import re
import asyncio
import aiohttp
import aria2p
import yt_dlp
import mimetypes
from helper_funcs.display import progress_for_pyrogram, humanbytes
from helper_funcs.ffmpeg import take_screen_shot, get_metadata
from plugins.command import USER_THUMBS, is_authorized

# --- MEMORY ---
TASKS = {}
aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800, secret=""))

# 🚀 TURBO TRACKERS
TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://tracker.tiny-vps.com:6969/announce",
    "udp://tracker.internetwarriors.net:1337/announce",
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://exodus.desync.com:6969/announce"
]

# 🎥 VIDEO EXTENSIONS
VIDEO_EXT = ('.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.3gp', '.ts', '.mpeg')

# --- 1. HELPER: GET YOUTUBE INFO ---
def get_yt_resolutions(url):
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'geo_bypass': True, 'noplaylist': True}
        if os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            formats_found = []
            seen_heights = set()
            for f in info['formats']:
                height = f.get('height')
                filesize = f.get('filesize') or f.get('filesize_approx')
                if height and height in [1080, 720, 480, 360] and height not in seen_heights:
                    size_text = humanbytes(filesize) if filesize else "N/A"
                    formats_found.append({"res": f"{height}p", "size": size_text, "height": height})
                    seen_heights.add(height)
            formats_found.sort(key=lambda x: x['height'], reverse=True)
            return title, formats_found
    except: return None, []

# --- 2. HELPER: DOWNLOADER ---
def run_ytdlp(url, quality_setting, output_path):
    ydl_opts = {'outtmpl': f'{output_path}/%(title)s.%(ext)s', 'quiet': True, 'geo_bypass': True, 'noplaylist': True}
    if os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'

    if quality_setting == "audio":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})
    else:
        ydl_opts.update({'format': f'bestvideo[height<={quality_setting}]+bestaudio/best[height<={quality_setting}]', 'merge_output_format': 'mp4'})

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = 'mp3' if quality_setting == 'audio' else 'mp4'
        return ydl.prepare_filename(info).rsplit('.', 1)[0] + f'.{ext}'

def find_largest_file(path):
    if os.path.isfile(path): return path
    largest_file, largest_size = None, 0
    for root, dirs, files in os.walk(path):
        for file in files:
            fp = os.path.join(root, file); fs = os.path.getsize(fp)
            if fs > largest_size: largest_size = fs; largest_file = fp
    return largest_file

# --- 3. ENTRY POINT ---
@Client.on_message(filters.private & (filters.regex(r'http') | filters.regex(r'magnet') | filters.document | filters.video | filters.audio))
async def incoming_task(client, message):
    user_id = message.from_user.id
    if not is_authorized(user_id): await message.reply_text("⚠️ Access Denied."); return

    url = None; is_torrent = False; is_youtube = False; is_tg_file = False; tg_obj = None; custom_name = None
    if message.document or message.video or message.audio:
        if message.document and str(message.document.file_name).endswith(".torrent"): is_torrent = True; url = await message.download()
        else:
            is_tg_file = True; tg_obj = message
            if message.document: custom_name = message.document.file_name
            elif message.video: custom_name = message.video.file_name or "video.mp4"
            elif message.audio: custom_name = message.audio.file_name or "audio.mp3"
    else:
        text = message.text.strip()
        found_url = re.search(r'(?P<url>https?://[^\s]+)', text)
        if found_url: url = found_url.group("url")
        elif text.startswith("magnet:"): url = text; is_torrent = True
        
        if url:
            if "youtube.com" in url or "youtu.be" in url:
                is_youtube = True
                if "/shorts/" in url: url = url.replace("/shorts/", "/watch?v=")
            elif "magnet" in url: is_torrent = True
            if "|" in text: 
                try: url, custom_name = text.split("|"); url=url.strip(); custom_name=custom_name.strip()
                except: pass

    if not url and not is_tg_file: return

    TASKS[user_id] = {
        "url": url, "is_torrent": is_torrent, "is_youtube": is_youtube, "is_tg_file": is_tg_file,
        "tg_obj": tg_obj, "custom_name": custom_name, "mode": "video", "yt_resolutions": [], 
        "gid": None, "chat_id": message.chat.id, "message_id": None
    }

    sent_msg = await message.reply_text("🔄 **Analyzing...**", quote=True)
    TASKS[user_id]["message_id"] = sent_msg.id

    if is_youtube:
        await sent_msg.edit("🔎 **Scanning YouTube...**")
        title, formats = await asyncio.to_thread(get_yt_resolutions, url)
        if not formats: await sent_msg.edit("❌ **YouTube Error.**\nCheck `cookies.txt` or Link."); del TASKS[user_id]; return
        TASKS[user_id]["yt_resolutions"] = formats; TASKS[user_id]["custom_name"] = title
        
    await show_dashboard(client, message.chat.id, sent_msg.id, user_id)

# --- 4. DASHBOARD ---
async def show_dashboard(client, chat_id, message_id, user_id):
    if user_id not in TASKS: return
    task = TASKS[user_id]
    name = task["custom_name"] if task["custom_name"] else "Default"
    buttons = []

    if task["is_youtube"]:
        text = f"📺 **YouTube Video Found**\n\n**Title:** `{name}`\n👇 **Select Quality:**"
        for fmt in task["yt_resolutions"]:
            buttons.append([InlineKeyboardButton(f"🎬 {fmt['res']} ({fmt['size']})", callback_data=f"yt_set_{fmt['height']}")])
        buttons.append([InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data="yt_set_audio")])
        buttons.append([InlineKeyboardButton("✏️ Rename", callback_data="ask_rename"), InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    elif task["is_tg_file"]:
        text = f"📂 **File Manager**\n**Name:** `{name}`\n👇 **Rename or Upload:**"
        buttons = [[InlineKeyboardButton("✏️ Rename", callback_data="ask_rename")],
                   [InlineKeyboardButton("▶️ Process", callback_data="start_process"), InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
    else:
        if task["mode"] == "video":
             mode_txt = "Streamable (Risk of Lag/Corruption)"
             sw_btn = "🛡️ Use Safe Mode (Recommended)"
        else:
             mode_txt = "Safe File Mode (Best for VLC)"
             sw_btn = "🎥 Try Stream Mode"

        text = f"⚙️ **Link Dashboard**\n**Source:** {'🧲 Torrent' if task['is_torrent'] else '🔗 Link'}\n**Name:** `{name}`\n**Mode:** {mode_txt}"
        buttons = [[InlineKeyboardButton(sw_btn, callback_data="toggle_mode"), InlineKeyboardButton("✏️ Rename", callback_data="ask_rename")],
                   [InlineKeyboardButton("▶️ Start Download", callback_data="start_process"), InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]

    try: await client.edit_message_text(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup(buttons))
    except: pass

# --- 5. BUTTONS ---
@Client.on_callback_query()
async def handle_buttons(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    # 🛑 FIXED CLEANUP CRASH HERE
    if data == "cancel" or data == "cancel_task":
        if user_id in TASKS:
            gid = TASKS[user_id].get("gid")
            if gid:
                try: 
                    aria2.client.remove(gid)
                    aria2.client.force_remove(gid)
                except: pass
            del TASKS[user_id]
        await query.message.edit("❌ **Task Cancelled.**")
        return

    if user_id not in TASKS: await query.answer("❌ Expired.", show_alert=True); return

    if data.startswith("yt_set_"):
        TASKS[user_id]["mode"] = data.split("_")[2]
        await query.message.edit(f"✅ Selected: **{TASKS[user_id]['mode']}**\n🚀 **Starting Download...**")
        await process_task(client, query.message, user_id)
        return

    if data == "toggle_mode":
        TASKS[user_id]["mode"] = "document" if TASKS[user_id]["mode"] == "video" else "video"
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)
    elif data == "ask_rename":
        TASKS[user_id]["state"] = "waiting_for_name"
        await query.message.edit("📝 **Send new name:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]]))
    elif data == "back_to_menu":
        TASKS[user_id]["state"] = "menu"
        await show_dashboard(client, query.message.chat.id, query.message.id, user_id)
    elif data == "start_process":
        await query.message.edit("🚀 **Starting...**")
        await process_task(client, query.message, user_id)

# --- 6. PROCESSOR ---
async def process_task(client, status_msg, user_id):
    task = TASKS[user_id]
    url, custom_name, mode = task["url"], task["custom_name"], task["mode"]
    download_path, start_time = "downloads/", time.time()
    if not os.path.exists(download_path): os.makedirs(download_path)
    final_path = None

    try:
        if task["is_youtube"]:
            await status_msg.edit(f"⬇️ **Downloading YouTube ({mode})...**")
            final_path = await asyncio.to_thread(run_ytdlp, url, mode, download_path)
        
        elif task["is_torrent"]:
            if "magnet:?" in url: 
                for tr in TRACKERS: url += f"&tr={tr}"
            
            dl_opts = {'dir': os.path.abspath(download_path), 'file-allocation': 'none', 'max-connection-per-server': '4', 'seed-time': '0'}
            if os.path.isfile(url): dl = aria2.add_torrent(url, options=dl_opts)
            else: dl = aria2.add_magnet(url, options=dl_opts)
            if os.path.isfile(url): os.remove(url)

            TASKS[user_id]["gid"] = dl.gid
            
            while not dl.is_complete:
                if user_id not in TASKS: return
                dl.update()
                if dl.status == 'error': await status_msg.edit("❌ Torrent Error."); return
                
                if dl.total_length > 0:
                    done, total = dl.completed_length, dl.total_length
                    percent = (done / total) * 100
                    speed = humanbytes(dl.download_speed)
                    bar = "■" * int(percent / 10) + "□" * (10 - int(percent / 10))
                    msg = (f"⬇️ **Torrent...**\n💾 `{humanbytes(done)}` / `{humanbytes(total)}`\n"
                           f"⚡ `{speed}/s` | 👥 `{dl.connections}`\n⏳ [{bar}] `{round(percent, 2)}%`")
                    try: await status_msg.edit(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]]))
                    except: pass
                await asyncio.sleep(4)
            
            search_path = str(dl.files[0].path) if dl.files else download_path
            final_path = find_largest_file(search_path)
            if not final_path: final_path = find_largest_file(download_path)
            if not final_path: await status_msg.edit("❌ **Error:** No file found."); return

        elif task["is_tg_file"]:
            await status_msg.edit("⬇️ **Downloading File...**")
            final_path = await client.download_media(task["tg_obj"], file_name=download_path, progress=progress_for_pyrogram, progress_args=("⬇️ Downloading...", status_msg, start_time))
        else:
            fname = custom_name if custom_name else url.split("/")[-1]
            final_path = os.path.join(download_path, fname)
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url) as resp:
                    with open(final_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024*1024); if not chunk: break; f.write(chunk)

        # RENAME
        if user_id not in TASKS: return
        if not final_path or not os.path.exists(final_path): await status_msg.edit("❌ **Error:** File vanished."); return
        if custom_name and not task["is_youtube"]:
            ext = os.path.splitext(final_path)[1]
            if not os.path.splitext(custom_name)[1]: custom_name += ext
            new_path = os.path.join(os.path.dirname(final_path), custom_name)
            try: os.rename(final_path, new_path); final_path = new_path
            except: pass

        fname = os.path.basename(final_path)
        thumb_path = USER_THUMBS.get(user_id)
        
        # 📸 SCREENSHOT: Only if VIDEO mode
        if mode == "video" and not thumb_path and fname.lower().endswith(VIDEO_EXT):
            try: thumb_path = await take_screen_shot(final_path, download_path, 10)
            except: pass

        await status_msg.edit("📤 **Uploading...**")
        mime_type, _ = mimetypes.guess_type(final_path)
        
        if mode == "video" or (task["is_youtube"] and mode != "audio"):
            try:
                w, h, dur = await get_metadata(final_path)
                await client.send_video(
                    status_msg.chat.id, final_path, caption=f"🎥 **{fname}**", 
                    thumb=thumb_path, width=w, height=h, duration=dur, 
                    supports_streaming=True, mime_type=mime_type,
                    progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_time)
                )
            except:
                await client.send_document(status_msg.chat.id, final_path, caption=f"📂 **{fname}**", thumb=thumb_path, progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_time))
        elif mode == "audio" or fname.endswith(".mp3"):
            await client.send_audio(status_msg.chat.id, final_path, caption=f"🎵 **{fname}**", thumb=thumb_path, progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_time))
        else:
            await client.send_document(status_msg.chat.id, final_path, caption=f"📂 **{fname}**", thumb=thumb_path, progress=progress_for_pyrogram, progress_args=("📤 Uploading...", status_msg, start_time))

        # CLEANUP & DELETE
        if os.path.exists(final_path): os.remove(final_path)
        if thumb_path and "thumbs/" not in thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)
        
        if TASKS[user_id].get("gid"): 
            try: 
                aria2.client.remove(TASKS[user_id]["gid"])
                aria2.client.force_remove(TASKS[user_id]["gid"])
            except: pass
            
        await status_msg.delete() # SAFE DELETE
        del TASKS[user_id]
        
    except Exception as e:
        try: await status_msg.edit(f"❌ **Error:** {e}")
        except: pass
        if user_id in TASKS: del TASKS[user_id]
