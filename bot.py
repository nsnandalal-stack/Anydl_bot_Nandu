import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, OWNER_ID, DOWNLOAD_DIR
from downloader import start_download, stop_download, download_status


def owner_only(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == OWNER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        await update.message.reply_text("❌ Not authorized.")
        return

    await update.message.reply_text(
        "✅ Torrent Bot Ready\n\n"
        "Send a magnet link to start download.\n\n"
        "/status – check progress\n"
        "/stop – stop download"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        return

    await update.message.reply_text(download_status())


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        return

    if stop_download():
        await update.message.reply_text("🛑 Download stopped.")
    else:
        await update.message.reply_text("ℹ️ No active download.")


async def magnet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_only(update):
        return

    text = update.message.text.strip()

    if not text.startswith("magnet:"):
        await update.message.reply_text("❌ Send a valid magnet link.")
        return

    ok, msg = start_download(text, DOWNLOAD_DIR)
    await update.message.reply_text("⬇️ " + msg)


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, magnet_handler))

    print("✅ Bot running (Python 3.11)")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
