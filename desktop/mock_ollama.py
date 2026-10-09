"""TEST ONLY: fake Ollama API to exercise the packaged desktop HTTP bridge."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
SENTINEL="PACE desktop local integration test passed"
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path!="/api/chat":
            self.send_error(404);return
        try:
            body=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))))
            assert body["stream"] is True and body["model"]=="qwen2.5-coder:1.5b"
        except (ValueError,KeyError,AssertionError):
            self.send_error(400);return
        self.send_response(200)
        self.send_header("Content-Type","application/x-ndjson")
        self.end_headers()
        for item in ({"message":{"content":SENTINEL},"done":False},{"message":{"content":""},"done":True}):
            self.wfile.write((json.dumps(item)+"\n").encode());self.wfile.flush()
    def log_message(self,*args):
        pass
if __name__=="__main__":
    ThreadingHTTPServer(("127.0.0.1",11434),Handler).serve_forever()
