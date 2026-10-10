"""Validated provider gateway. Emits *real* output, never generated placeholders.

Hugging Face Gradio generator outputs are snapshots; this adapter yields only deltas.
The legacy v4 orchestrators are intentionally not called because some had fake
fallbacks and swallowed provider errors. Local actor/critic uses the actual models.
"""
from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import Iterator

from core.config import get_settings

log = logging.getLogger(__name__)


class AIUnavailable(RuntimeError):
    """Inference cannot be completed; user-facing message must stay generic."""


def ensure_provider_configured() -> None:
    settings = get_settings()
    if settings.ai_provider == "disabled":
        raise AIUnavailable("AI inference is disabled")
    if settings.ai_provider == "huggingface" and not settings.hf_space_id:
        raise AIUnavailable("Hugging Face Space is not configured")


def model_source(speed: str) -> str:
    settings = get_settings()
    if settings.ai_provider == "ollama":
        return "ollama-same-model-review" if speed == "pro" else "ollama-single-model"
    if settings.ai_provider == "huggingface":
        return "huggingface-single-model-review" if speed == "pro" else "huggingface-single-model"
    return "local-actor-critic" if speed == "pro" else "local-actor"


@lru_cache(maxsize=3)
def _hf_client(space_id: str, token: str):
    from gradio_client import Client
    return Client(space_id, token=token or None)


def _huggingface_stream(text: str, mode: str, speed: str) -> Iterator[str]:
    settings = get_settings()
    started = time.monotonic()
    # The Space is public. Some HF ZeroGPU identities have separate quotas.
    # Retry anonymously only if an authenticated job failed before any output.
    attempts = [(settings.hf_token, "/generate")]
    if settings.hf_token:
        attempts.append(("", "/generate"))
    # CPU inference is a real model execution endpoint, not a canned answer.
    # It bypasses the ZeroGPU queue when Render's shared egress identity is denied.
    attempts.append(("", "/generate_cpu"))
    for attempt, (credential, api_name) in enumerate(attempts):
        job = None
        last = ""
        try:
            client = _hf_client(settings.hf_space_id, credential)
            job = client.submit(text, mode, speed, settings.max_new_tokens, api_name=api_name)
            for snapshot in job:
                if time.monotonic() - started > settings.ai_timeout_seconds:
                    raise AIUnavailable("AI request exceeded its deadline")
                if not isinstance(snapshot, str):
                    raise AIUnavailable("Invalid AI service output")
                if len(snapshot) > 100_000:
                    raise AIUnavailable("AI output exceeded the safety limit")
                if not snapshot.startswith(last):
                    raise AIUnavailable("AI service stream was not append-only")
                delta = snapshot[len(last):]
                if delta:
                    yield delta
                last = snapshot
            if last.strip():
                return
            status = job.status()
            log.warning(
                "Hosted AI returned no tokens (status=%s, success=%s, attempt=%s, authenticated=%s)",
                getattr(status, "code", None),
                getattr(status, "success", None),
                attempt + 1,
                bool(credential),
            )
            if attempt + 1 < len(attempts):
                log.info("Retrying hosted inference using next provider path")
                continue
            raise AIUnavailable("Hosted AI job finished without a response")
        except AIUnavailable:
            raise
        except Exception as exc:
            log.warning("Hosted AI client failed (class=%s, authenticated=%s)", type(exc).__name__, bool(credential))
            if attempt + 1 < len(attempts) and not last:
                continue
            raise AIUnavailable("AI service unavailable or quota exhausted") from exc
        finally:
            if job is not None and not job.done():
                try:
                    job.cancel()
                except Exception:
                    pass


def stream_generate(text: str, mode: str, speed: str) -> Iterator[str]:
    ensure_provider_configured()
    settings = get_settings()
    if settings.ai_provider == "huggingface":
        yield from _huggingface_stream(text, mode, speed)
    elif settings.ai_provider == "ollama":
        from masteries.services.ollama_provider import stream_ollama
        yield from stream_ollama(text, mode, speed)
    elif settings.ai_provider == "local":
        try:
            from masteries.services.local_ensemble import stream_local_ensemble
            yield from stream_local_ensemble(text, mode, speed)
        except AIUnavailable:
            raise
        except Exception as exc:
            log.exception("Local inference failure")
            raise AIUnavailable("Local AI unavailable") from exc
    else:
        raise AIUnavailable("Unsupported model configuration")


def generate(text: str, mode: str, speed: str) -> tuple[str, str]:
    content = "".join(stream_generate(text, mode, speed))
    if not content.strip():
        raise AIUnavailable("AI model returned no content")
    return content, model_source(speed)
