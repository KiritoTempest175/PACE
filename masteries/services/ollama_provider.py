"""OpenAI-independent local Ollama streaming provider for CPU / RTX 4060.

Local Ollama must be explicitly configured. No model output is synthesized.
Review mode makes a second pass with the same model and is labeled as such.
"""
from __future__ import annotations

import json
import os
from typing import Iterator
from urllib.parse import urlsplit

import httpx

from core.config import get_settings
from masteries.services.ai_gateway import AIUnavailable


def desktop_role_model(role: str) -> str | None:
    """Return the user's persisted local Generator or Reviewer selection."""
    if not os.environ.get("PACE_DESKTOP_DATA_DIR"):
        return None
    from desktop.model_manager import read_selection
    model = read_selection().get(role)
    if not model:
        raise AIUnavailable(f"Download and select a {role} model in PACE Desktop setup")
    return model


def _request(prompt: str, mode: str, role: str = "actor") -> Iterator[str]:
    settings = get_settings()
    url = urlsplit(settings.ollama_base_url)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
        raise AIUnavailable("Invalid local Ollama configuration")
    system = {
        "coding": "Write correct code. Do not claim execution or testing.",
        "literacy": "Answer only from supplied excerpts; state when evidence is insufficient.",
        "research": "Give tentative explanations. Do not fabricate citations.",
    }[mode]
    payload = {
        "model": desktop_role_model(role) or settings.ollama_model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "stream": True,
        "options": {"num_predict": settings.max_new_tokens},
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(connect=5, read=settings.ai_timeout_seconds, write=10, pool=5)) as client:
            with client.stream("POST", settings.ollama_base_url.rstrip("/") + "/api/chat", json=payload) as response:
                response.raise_for_status()
                finished = False
                for line in response.iter_lines():
                    if not line:
                        continue
                    event = json.loads(line)
                    if "error" in event:
                        raise AIUnavailable("Ollama returned an error")
                    chunk = event.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if event.get("done"):
                        finished = True
                if not finished:
                    raise AIUnavailable("Local model stream ended unexpectedly")
    except AIUnavailable:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise AIUnavailable("Local Ollama model is not reachable") from exc


def stream_ollama(text: str, mode: str, speed: str) -> Iterator[str]:
    if speed == "fast":
        yield from _request(text, mode)
        return
    # The first pass is intentionally buffered: it is not final reviewed output.
    draft = "".join(_request(text, mode, "actor")).strip()
    if not draft:
        raise AIUnavailable("Local actor output is empty")
    review = "Review this draft for mistakes and return only the corrected answer. " \
             "State any uncertainty.\n\nQUESTION:\n" + text + "\n\nDRAFT:\n" + draft
    yield from _request(review, mode, "critic")
