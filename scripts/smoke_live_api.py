"""Exercise the deployed PACE API + Hugging Face provider + Neon persistence."""
from __future__ import annotations
import json
import secrets
import time
import urllib.error
import urllib.request

BASE = "https://pace-phase2-api.onrender.com"
TOKEN = secrets.token_hex(32)

def request(path, method="GET", data=None):
    headers = {"X-PACE-Session": TOKEN, "User-Agent": "PACE-deployment-smoketest/1.0"}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    return urllib.request.urlopen(req, timeout=190)

def check():
    health = {}
    for attempt in range(12):
        try:
            with request("/health") as res:
                health = json.load(res)
            if health.get("ai_provider") == "huggingface" and health.get("ai_configured"):
                break
            print("Backend waiting for HF configuration, current:", health, flush=True)
        except Exception as exc:
            print("Backend warming:", type(exc).__name__, flush=True)
        if attempt == 11:
            raise RuntimeError("Render never reported configured Hugging Face provider")
        time.sleep(10)
    print("HEALTH: configured Hugging Face provider", flush=True)
    chat_id = None
    try:
        with request("/generate", "POST", {"text": "Reply with only the word hello.", "mode": "coding", "speed_mode": "fast"}) as response:
            assert response.status == 200
            raw = response.read().decode("utf-8")
        events = []
        for line in raw.replace("\r\n", "\n").splitlines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
        init = next((e for e in events if e.get("type") == "init"), None)
        chat_id = init.get("conversation_id") if init else None
        errors = [e.get("content") for e in events if e.get("type") == "error"]
        if errors:
            raise RuntimeError(f"Model stream returned error events: {errors}")
        text_chunks = [e.get("content") for e in events if e.get("type") == "token"]
        if not text_chunks or not "".join(text_chunks).strip():
            raise RuntimeError("No model tokens received")
        if not any(e.get("type") == "done" for e in events):
            raise RuntimeError("SSE response missing done event")
        assert init and "huggingface" in init.get("source", "")
        print("SSE: model response received and done event verified; chars:", len("".join(text_chunks)), flush=True)
        with request("/conversations/" + chat_id) as res:
            stored = json.load(res)
        messages = stored.get("messages", [])
        assert any(m.get("role") == "user" for m in messages)
        assert any(m.get("role") == "assistant" and m.get("status") == "completed" for m in messages)
        print("NEON: persisted user and assistant messages are readable", flush=True)
    finally:
        if chat_id:
            with request("/conversations/" + chat_id, method="DELETE") as res:
                assert res.status == 200
            print("CLEANUP: smoke-test conversation deleted", flush=True)

if __name__ == "__main__":
    check()
