from pyrogram import Client
from os import environ
import logging
from aiohttp import web
import asyncio

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)

# 2. Load Secrets
API_ID = int(environ.get("API_ID", 0))
API_HASH = environ.get("API_HASH")
BOT_TOKEN = environ.get("BOT_TOKEN")
PORT = int(environ.get("PORT", 8000))

# 3. Define the Bot
app = Client(
    "anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
    ipv6=False,
    in_memory=True
)

# 4. Fake Web Server (Koyeb Fix)
async def web_server():
    async def handle(request):
        return web.Response(text="Bot is Running!")

    server = web.Application()
    server.router.add_get("/", handle)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🕸️ Fake Web Server started on Port {PORT}")

# 5. Run Everything
async def main():
    print("⚡ Starting Bot + Web Server...")
    await app.start()
    await web_server()
    print("✅ Bot Started Successfully!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        print(f"❌ Error: {e}")
