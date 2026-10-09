"""Compatibility entrypoint for the original PACE literacy actor/critic API.

This module deliberately contains no pseudo-code, fabricated approval, or
model-unavailable success fallback. Errors propagate as explicit error events.
"""
from masteries.services.local_ensemble import _actor, _critic, stream_local_ensemble
from masteries.services.ai_gateway import AIUnavailable


def get_actor():
    return _actor("literacy")


def get_critic():
    return _critic("literacy")


def flush_vram():
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        return


def literacy_pipeline(user_prompt: str, max_iterations: int = 1, speed_mode: str = "pro"):
    if max_iterations != 1:
        yield {"type": "error", "content": "Only one revision cycle is supported"}
        return
    try:
        yield {"type": "status", "content": "Running real local model pipeline"}
        for chunk in stream_local_ensemble(user_prompt, "literacy", speed_mode):
            yield {"type": "token", "content": chunk}
        yield {"type": "status", "content": "Local inference completed"}
    except (AIUnavailable, Exception):
        yield {"type": "error", "content": "Local model inference failed"}
