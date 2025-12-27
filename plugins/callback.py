from pyrogram import Client
from pyrogram.types import CallbackQuery
import os

@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    
    # --- CANCEL BUTTON ---
    if data == "cancel":
        try:
            # This edits the message to show it was cancelled
            await query.message.edit_text("❌ Task Cancelled by User.")
            # Note: This stops the interface updates. 
            # (Stopping the actual background download requires complex task management, 
            # but this stops the spam).
        except:
            pass

    # --- RENAME HELP BUTTON ---
    elif data == "rename_help":
        # Shows a pop-up alert with instructions
        await query.answer(
            "📝 How to Rename:\n\n"
            "Send the link followed by ' | ' and the new name.\n\n"
            "Example:\n"
            "www.example.com/video.mp4 | MyMovie.mp4",
            show_alert=True
        )
