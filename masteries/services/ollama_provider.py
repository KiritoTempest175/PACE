"""Ollama local provider with bounded automatic continuation and truthful review semantics."""
from __future__ import annotations

import json
from typing import Iterator
from urllib.parse import urlsplit

import httpx

from core.config import get_settings
from masteries.services.ai_gateway import AIUnavailable


def _request(prompt: str, mode: str) -> Iterator[str]:
    settings = get_settings()
    url = urlsplit(settings.ollama_base_url)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
        raise AIUnavailable("Invalid local Ollama configuration")
    system = {
        "coding": "Write complete executable code. Do not claim execution or testing.",
        "literacy": "Answer only from supplied excerpts; state when evidence is insufficient.",
    }[mode]
    payload = {
        "model": settings.ollama_model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "stream": True,
        "options": {"num_predict": settings.max_new_tokens},
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(connect=5, read=settings.ai_timeout_seconds, write=10, pool=5)) as client:
            with client.stream("POST", settings.ollama_base_url.rstrip("/") + "/api/chat", json=payload) as response:
                response.raise_for_status()
                finished = False
                reason = None
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
                        reason = event.get("done_reason", "stop")
                if not finished:
                    raise AIUnavailable("Local model stream ended unexpectedly")
                return reason
    except AIUnavailable:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise AIUnavailable("Local Ollama model is not reachable") from exc


def _overlap(previous: str, continuation: str) -> int:
    """Longest suffix/prefix overlap; avoid repeating code when stitching."""
    boundary = min(2048, len(previous), len(continuation))
    for count in range(boundary, 0, -1):
        if previous.endswith(continuation[:count]):
            return count
    return 0


def _complete(prompt: str, mode: str) -> Iterator[str]:
    settings = get_settings()
    full = ""
    for attempt in range(settings.max_continuation_rounds + 1):
        # Keep the first pass streaming. Buffer subsequent rounds to dedupe boundaries.
        pieces = []
        iterator = _request(prompt, mode)
        while True:
            try:
                chunk = next(iterator)
            except StopIteration as completed:
                reason = completed.value
                break
            pieces.append(chunk)
            if attempt == 0:
                full += chunk
                yield chunk
        if attempt:
            continuation = "".join(pieces)
            fresh = continuation[_overlap(full, continuation):]
            full += fresh
            if fresh:
                yield fresh
        if reason != "length" and full.count("```") % 2 == 0:
            return
        if attempt >= settings.max_continuation_rounds:
            raise AIUnavailable("Generation reached the configured continuation limit; request Continue in the app")
        context_tail = full[-5000:]
        prompt = (
            "Continue precisely where the prior answer stopped. Do not repeat any text. "
            "Close any unfinished code fence. Answer only with the missing continuation.\n\n"
            "PREVIOUS END:\n" + context_tail
        )
        if (len(prompt) + 2) // 3 > settings.max_prompt_tokens_estimate:
            raise AIUnavailable("Continuation would exceed the configured model context budget")


def stream_ollama(text: str, mode: str, speed: str) -> Iterator[str]:
    if speed == "fast":
        yield from _complete(text, mode)
        return
    draft = "".join(_complete(text, mode)).strip()
    if not draft:
        raise AIUnavailable("Local actor output is empty")
    review = (
        "Review this draft for mistakes and return the complete corrected answer. "
        "Do not omit files or code blocks. State uncertainty.\n\nQUESTION:\n" + text +
        "\n\nDRAFT:\n" + draft
    )
    if (len(review) + 2) // 3 > get_settings().max_prompt_tokens_estimate:
        raise AIUnavailable("Pro review exceeds the model context budget; shorten the prompt")
    yield from _complete(review, mode)
