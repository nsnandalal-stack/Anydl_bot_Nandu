from pyrogram import Client
from os import environ
import logging
from aiohttp import web
import asyncio
import os

logging.basicConfig(level=logging.INFO)

API_ID = int(environ.get("API_ID", 0))
API_HASH = environ.get("API_HASH")
BOT_TOKEN = environ.get("BOT_TOKEN")
PORT = int(environ.get("PORT", 8000))

app = Client(
    "anydl_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
    ipv6=False,
    in_memory=True
)

async def web_server():
    async def handle(request):
        return web.Response(text="Bot is Alive!")
    server = web.Application()
    server.router.add_get("/", handle)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🕸️ Fake Web Server started on Port {PORT}")

async def main():
    print("⚡ Starting Aria2 (Torrent Engine)...")
    # This line is REQUIRED for Torrents to work
    os.system("aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --daemon")
    
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
