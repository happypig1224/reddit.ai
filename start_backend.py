"""
Reddit Karma Pilot - Backend Launcher
"""

import sys
import uvicorn

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    from app.core.config import settings
    port = settings.SERVER_PORT
    print(f"🚀 Starting Reddit Karma Pilot Backend on http://127.0.0.1:{port} ...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)

