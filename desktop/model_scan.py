"""Bounded, read-only discovery of known local model caches.

Discovery does not imply runnable inference. Model files are never opened or uploaded.
"""
from __future__ import annotations
import os
import re
from pathlib import Path

_EXTENSIONS = {".gguf", ".safetensors"}
_QUANT = re.compile(r"(Q[2-8]_[A-Z0-9_]+|F16|BF16|FP16|FP32)", re.IGNORECASE)

def model_roots(home: Path | None = None) -> list[Path]:
    root = home or Path.home()
    paths = [
        root / ".lmstudio" / "models",
        root / ".cache" / "huggingface" / "hub",
        root / ".ollama" / "models",
        root / "models",
        root / "Models",
        root / "Documents" / "models",
        root / "Downloads" / "models",
    ]
    if os.environ.get("HF_HOME"):
        paths.append(Path(os.environ["HF_HOME"]) / "hub")
    if os.environ.get("OLLAMA_MODELS"):
        paths.append(Path(os.environ["OLLAMA_MODELS"]))
    return list(dict.fromkeys(paths))

def scan_models(roots: list[Path] | None = None, limit: int = 150) -> list[dict]:
    discovered = []
    for root in roots if roots is not None else model_roots():
        if not root.is_dir() or root.is_symlink():
            continue
        stack = [(root, 0)]
        examined = 0
        while stack and len(discovered) < limit and examined < 10000:
            folder, depth = stack.pop()
            try:
                for item in folder.iterdir():
                    examined += 1
                    if examined > 10000:
                        break
                    if item.is_symlink():
                        continue
                    if item.is_dir() and depth < 5:
                        stack.append((item, depth+1))
                    elif item.is_file() and item.suffix.lower() in _EXTENSIONS:
                        size = item.stat().st_size
                        quant = _QUANT.search(item.name)
                        discovered.append({
                            "name": item.name,
                            "path": str(item),
                            "format": item.suffix.lstrip(".").lower(),
                            "size_bytes": size,
                            "size_gb": round(size / (1024**3), 2),
                            "quantization": quant.group(0) if quant else "unknown",
                            "vram_fit": "unknown (no measured available VRAM)",
                            "loadable": False,
                            "note": "Detected on disk; direct GGUF/safetensors loading is not verified. Use Ollama to run compatible models.",
                        })
                        if len(discovered) >= limit:
                            break
            except (PermissionError, FileNotFoundError, OSError):
                continue
    return discovered
