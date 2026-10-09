"""Packaged PACE FastAPI sidecar. Launch only through the Tauri desktop host.

Run as a loopback-only process, with a per-launch unpredictable capability
header. Store the SQLite database and transient upload files under the user's
local application data directory, never under the installation directory.

No model weights are bundled; local inference uses user-installed Ollama.
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

def configure() -> tuple[int, str]:
    port = int(os.environ["PACE_DESKTOP_PORT"])
    key = os.environ["PACE_DESKTOP_KEY"]
    if not 1024 <= port <= 65535 or len(key) != 64:
        raise RuntimeError("Invalid desktop launch configuration")
    if any(ch not in "0123456789abcdef" for ch in key):
        raise RuntimeError("Invalid desktop capability token")
    root = Path(os.environ["PACE_DESKTOP_DATA_DIR"]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "uploads").mkdir(parents=True, exist_ok=True)
    # PyInstaller --noconsole sets stdout/stderr to None on Windows.
    # Uvicorn and its logging dependencies still require writable streams.
    # Keep diagnostic output local, never print the ephemeral API key.
    log = (root / "pace-backend.log").open("a", encoding="utf-8", buffering=1)
    sys.stdout = log
    sys.stderr = log
    # Always override untrusted environment configuration in this sidecar.
    os.environ.update({
        "ENVIRONMENT": "development",
        "AI_PROVIDER": "ollama",
        "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
        "OLLAMA_MODEL": "qwen2.5-coder:1.5b",
        "DATABASE_URL": "sqlite:///" + (root / "pace.sqlite3").as_posix(),
        "UPLOAD_DIR": str(root / "uploads"),
        "SANDBOX_ENABLED": "false",
        "CORS_ORIGINS": "http://tauri.localhost,https://tauri.localhost,tauri://localhost",
    })
    return port, key

def make_app(key: str):
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from backend.main import app

    @app.middleware("http")
    async def desktop_auth(request: Request, call_next):
        # CORS preflight is handled independently. All real requests,
        # including health checks, must prove they came from this app.
        if request.method != "OPTIONS" and not secrets.compare_digest(
            request.headers.get("X-PACE-Desktop-Key", ""), key
        ):
            return JSONResponse({"detail": "Desktop capability required"}, status_code=401)
        return await call_next(request)

    return app

if __name__ == "__main__":
    port, key = configure()
    import uvicorn
    uvicorn.run(make_app(key), host="127.0.0.1", port=port, log_level="warning", access_log=False)
