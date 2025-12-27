from pyrogram import Client
from pyrogram.types import CallbackQuery

@Client.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    
    # Cancel Button Logic
    if data == "cancel":
        try:
            await query.message.edit_text("❌ Task Cancelled by User.")
        except:
            pass

    # Rename Help Button Logic
    elif data == "rename_help":
        await query.answer(
            "📝 **How to Rename:**\n\n"
            "Send the link followed by ' | ' and the new name.\n\n"
            "Example:\n"
            "http://example.com/video.mp4 | MyMovie.mp4",
            show_alert=True
        )
