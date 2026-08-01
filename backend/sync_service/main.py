import sys
import asyncio

# Windows needs the Proactor event loop specifically to support subprocess
# creation, which launching a headless browser requires under the hood.
# Setting this explicitly here (before anything else runs) avoids relying
# on whatever uvicorn's default happens to pick.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import os
import traceback
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv

from sync import run_sync

load_dotenv()

app = FastAPI(title="Taoyuan LTC Navigator — Facility Sync Service")

SYNC_SECRET_TOKEN = os.environ.get("SYNC_SECRET_TOKEN")
OPENCAGE_API_KEY = os.environ.get("OPENCAGE_API_KEY")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sync")
async def trigger_sync(token: str = Query(..., description="Shared secret, set as SYNC_SECRET_TOKEN")):
    """
    Triggered by an external cron pinger (e.g. cron-job.org) hitting this
    URL with the secret token monthly. GET is used (not POST) purely so
    it's trivial to configure in cron-job.org's UI, which pings a plain
    URL -- this is an accepted tradeoff for an internal admin trigger
    that's not part of any public-facing API surface.
    """
    if not SYNC_SECRET_TOKEN:
        raise HTTPException(status_code=500, detail="SYNC_SECRET_TOKEN not configured on server")
    if token != SYNC_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not OPENCAGE_API_KEY:
        raise HTTPException(status_code=500, detail="OPENCAGE_API_KEY not configured on server")

    try:
        result = await run_sync(OPENCAGE_API_KEY)
    except Exception as e:
        traceback.print_exc()  # full traceback goes to the terminal/Render logs
        raise HTTPException(
            status_code=502,
            detail=f"Sync failed: {type(e).__name__}: {e}",
        )

    return result


if __name__ == "__main__":
    # Run this via `python main.py` instead of the uvicorn CLI -- this
    # guarantees the Proactor policy above is set before uvicorn creates
    # its event loop, which `python -m uvicorn` doesn't reliably do.
    # Confirmed this matters in practice: switching to this run method
    # fixed a NotImplementedError that persisted even after moving to
    # Playwright's async API.
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Render sets PORT; defaults to 8000 locally
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
