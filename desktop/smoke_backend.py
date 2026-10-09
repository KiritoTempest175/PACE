"""Verify the actual frozen Windows backend can start and persist chats."""
from __future__ import annotations
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

def main():
    binary = Path(sys.argv[1]).resolve()
    assert binary.is_file(), binary
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    secret = secrets.token_hex(32)
    user_token = secrets.token_hex(32)
    with tempfile.TemporaryDirectory(prefix="pace-local-smoke-") as directory:
        env = dict(os.environ)
        env.update({
            "PACE_DESKTOP_PORT": str(port),
            "PACE_DESKTOP_KEY": secret,
            "PACE_DESKTOP_DATA_DIR": directory,
        })
        proc = subprocess.Popen([str(binary)], env=env, cwd=directory)
        try:
            origin = f"http://127.0.0.1:{port}"
            def req(path, method="GET", body=None, valid=True):
                headers={"X-PACE-Session": user_token}
                if valid:
                    headers["X-PACE-Desktop-Key"] = secret
                data=json.dumps(body).encode() if body is not None else None
                if data is not None:
                    headers["Content-Type"] = "application/json"
                return urllib.request.urlopen(
                    urllib.request.Request(origin + path, data=data,
                                           method=method, headers=headers),
                    timeout=8)
            for i in range(55):
                if proc.poll() is not None:
                    raise RuntimeError(f"Frozen backend exited with {proc.returncode}")
                try:
                    with req("/health") as response:
                        health = json.load(response)
                    break
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(1)
            else:
                raise RuntimeError("Frozen backend did not start within 55s")
            assert health["status"]=="healthy", health
            assert health["ai_provider"]=="ollama", health
            try:
                req("/health", valid=False)
            except urllib.error.HTTPError as e:
                assert e.code == 401
            else:
                raise RuntimeError("Desktop auth check did not reject missing key")
            with req("/conversations","POST",{"title":"Windows smoke","workspace":"coding"}) as resp:
                item=json.load(resp)
            with req("/conversations/"+item["id"]) as resp:
                record=json.load(resp)
            assert record["title"]=="Windows smoke"
            with req("/conversations/"+item["id"],"DELETE") as resp:
                assert resp.status == 200
            assert (Path(directory)/"pace.sqlite3").exists()
            print("PASS: frozen backend startup, scoped auth, SQLite persistence, CRUD and cleanup")
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=8)

if __name__=="__main__":
    main()
