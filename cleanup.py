import asyncio
import time
from config import DOWNLOAD_DIR, FILE_TTL_HOURS

async def cleanup_loop():
    while True:
        now = time.time()
        for path in DOWNLOAD_DIR.glob("*"):
            if path.is_dir():
                age = now - path.stat().st_mtime
                if age > FILE_TTL_HOURS * 3600:
                    for f in path.rglob("*"):
                        try:
                            f.unlink()
                        except Exception:
                            pass
                    try:
                        path.rmdir()
                    except Exception:
                        pass
        await asyncio.sleep(900)
