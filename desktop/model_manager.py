"""Desktop-only Ollama installer and model manager. Not mounted on hosted APIs."""
from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path
from threading import Lock
from urllib.request import Request, urlopen
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

CATALOG = (
    {"id":"llama3.2:1b","size":"1B","family":"Llama","use":"General / lightweight","gb":1.3},
    {"id":"llama3.2:3b","size":"3B","family":"Llama","use":"General","gb":2.0},
    {"id":"qwen2.5-coder:1.5b","size":"1.5B","family":"Qwen Coder","use":"Coding / lower RAM","gb":1.0},
    {"id":"qwen2.5-coder:3b","size":"3B","family":"Qwen Coder","use":"Coding / review","gb":1.9},
    {"id":"qwen2.5-coder:7b","size":"7B","family":"Qwen Coder","use":"Coding / stronger","gb":4.7},
    {"id":"gemma3:1b","size":"1B","family":"Gemma","use":"Lightweight general","gb":0.9},
    {"id":"gemma3:4b","size":"4B","family":"Gemma","use":"General / reasoning","gb":3.4},
    {"id":"qwen3:1.7b","size":"1.7B","family":"Qwen","use":"Compact general","gb":1.4},
    {"id":"qwen3:4b","size":"4B","family":"Qwen","use":"Intermediate general","gb":2.5},
    {"id":"qwen3:8b","size":"8B","family":"Qwen","use":"Stronger general","gb":5.2},
)
ALLOWED = frozenset(m["id"] for m in CATALOG)
DEFAULT_ACTOR = "qwen2.5-coder:1.5b"
DEFAULT_CRITIC = "qwen2.5-coder:3b"
_OLLAMA_URL = "http://127.0.0.1:11434"
_INSTALL_URL = "https://ollama.com/download/OllamaSetup.exe"
_lock = Lock()
router = APIRouter(prefix="/desktop/setup", tags=["desktop-only"])

def _root() -> Path:
    return Path(os.environ["PACE_DESKTOP_DATA_DIR"]).resolve()

def _selection_file() -> Path:
    return _root() / "models.json"

def read_selection() -> dict[str, str | None]:
    chosen = {"actor":None, "critic":None}
    try:
        data = json.loads(_selection_file().read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for role in chosen:
                if data.get(role) in ALLOWED:
                    chosen[role] = data[role]
    except (FileNotFoundError, ValueError, OSError, TypeError):
        pass
    return chosen

def _save_selection(data: dict[str, str | None]) -> None:
    target = _selection_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                     prefix=".models-", suffix=".tmp", delete=False) as f:
        temporary = Path(f.name)
        json.dump(data, f)
    try:
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)

def installed_models() -> list[str]:
    try:
        with httpx.Client(timeout=3) as client:
            r = client.get(_OLLAMA_URL + "/api/tags")
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])
                    if isinstance(m, dict) and isinstance(m.get("name"), str)]
    except (httpx.HTTPError, ValueError, KeyError):
        return []

def _ollama_binary() -> Path | None:
    import shutil
    found = shutil.which("ollama.exe") or shutil.which("ollama")
    paths = [Path(found)] if found else []
    if os.name == "nt":
        for key, parts in (("LOCALAPPDATA", ("Programs","Ollama","ollama.exe")),
                           ("PROGRAMFILES", ("Ollama","ollama.exe"))):
            if os.environ.get(key):
                paths.append(Path(os.environ[key]).joinpath(*parts))
    return next((path for path in paths if path.is_file()), None)

def _running() -> bool:
    try:
        return httpx.get(_OLLAMA_URL + "/api/version", timeout=2).is_success
    except httpx.HTTPError:
        return False

@router.get("/status")
def status():
    running = _running()
    names = installed_models() if running else []
    selected = read_selection()
    return {"installed":bool(_ollama_binary()) or running,"running":running,
            "installed_models":names,"selected":selected,"catalog":list(CATALOG),
            "actor_ready":bool(selected["actor"] and selected["actor"] in names),
            "critic_ready":bool(selected["critic"] and selected["critic"] in names)}

class ModelSelection(BaseModel):
    role: str
    model: str

def _validate(req: ModelSelection) -> None:
    if req.role not in ("actor","critic") or req.model not in ALLOWED:
        raise HTTPException(422,"Choose an available actor/reviewer model")

@router.post("/select")
def select_model(req: ModelSelection):
    _validate(req)
    if req.model not in installed_models():
        raise HTTPException(409,"Download this model in PACE before selecting it")
    with _lock:
        chosen = read_selection()
        chosen[req.role] = req.model
        _save_selection(chosen)
    return {"selected":chosen}

def _frame(event: dict) -> str:
    return "data: " + json.dumps(event,ensure_ascii=True) + "\n\n"

@router.post("/start")
def start_ollama():
    if _running():
        return {"status":"running"}
    executable = _ollama_binary()
    if not executable:
        raise HTTPException(404,"Ollama is not installed")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        subprocess.Popen([str(executable),"serve"], creationflags=flags,
                         stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,close_fds=True)
    except OSError:
        raise HTTPException(503,"Ollama could not start") from None
    return {"status":"starting"}

@router.post("/install")
def install_ollama():
    """After an explicit user click, download and open official Windows setup."""
    if os.name != "nt":
        raise HTTPException(501,"Automatic installer is supported on Windows")
    if _ollama_binary():
        return StreamingResponse(iter([_frame({"type":"already_installed"})]),media_type="text/event-stream")
    if not _lock.acquire(blocking=False):
        raise HTTPException(409,"A download or installation is already in progress")
    def events():
        destination = _root() / "installers" / "OllamaSetup.exe"
        destination.parent.mkdir(parents=True,exist_ok=True)
        temporary = destination.with_suffix(".download")
        try:
            request = Request(_INSTALL_URL,headers={"User-Agent":"PACE Desktop local setup"})
            with urlopen(request,timeout=45) as response, temporary.open("wb") as out:
                if not response.geturl().startswith("https://"):
                    raise RuntimeError("Insecure installer download redirect")
                total = int(response.headers.get("Content-Length") or 0)
                if total > 1024*1024*1024:
                    raise RuntimeError("Installer exceeds size limit")
                done=0
                while True:
                    chunk=response.read(256*1024)
                    if not chunk: break
                    done+=len(chunk)
                    if done>1024*1024*1024:
                        raise RuntimeError("Installer exceeds size limit")
                    out.write(chunk)
                    yield _frame({"type":"progress","status":"Downloading official Ollama installer",
                                  "completed":done,"total":total})
            with temporary.open("rb") as stream:
                header=stream.read(2)
            if done<100_000 or header!=b"MZ":
                raise RuntimeError("Invalid Windows installer content")
            os.replace(temporary,destination)
            subprocess.Popen([str(destination)],close_fds=True)
            yield _frame({"type":"installer_opened",
                          "message":"Complete Ollama's Windows installer, then return to PACE."})
        except Exception:
            yield _frame({"type":"error","message":"Could not download or launch Ollama. Check network access."})
        finally:
            temporary.unlink(missing_ok=True)
            _lock.release()
    return StreamingResponse(events(),media_type="text/event-stream")

@router.post("/pull")
def pull_model(req: ModelSelection):
    _validate(req)
    if not _running():
        raise HTTPException(503,"Start Ollama before downloading models")
    if not _lock.acquire(blocking=False):
        raise HTTPException(409,"Another model download is running")
    def events():
        try:
            with httpx.Client(timeout=httpx.Timeout(connect=5,read=180,write=20,pool=5)) as client:
                with client.stream("POST",_OLLAMA_URL+"/api/pull",
                                   json={"model":req.model,"stream":True}) as response:
                    response.raise_for_status()
                    finished=False
                    for line in response.iter_lines():
                        if not line: continue
                        event=json.loads(line)
                        if event.get("error"):
                            raise RuntimeError("Ollama download failed")
                        yield _frame({"type":"progress","status":str(event.get("status","Downloading model"))[:100],
                                      "total":int(event.get("total",0) or 0),
                                      "completed":int(event.get("completed",0) or 0)})
                        if event.get("status")=="success": finished=True
                    if not finished: raise RuntimeError("Missing download success confirmation")
            if req.model not in installed_models():
                raise RuntimeError("Model not registered by Ollama")
            chosen=read_selection()
            chosen[req.role]=req.model
            _save_selection(chosen)
            yield _frame({"type":"done","model":req.model,"role":req.role})
        except Exception:
            yield _frame({"type":"error","message":"Model download failed. Retry from PACE to resume."})
        finally:
            _lock.release()
    return StreamingResponse(events(),media_type="text/event-stream")
