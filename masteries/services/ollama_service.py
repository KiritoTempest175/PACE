"""
Ollama Service Module for PACE
Provides streaming and non-streaming completions using local Ollama models (e.g. llama3.2:1b).
"""

import os
from typing import Generator, Dict, Any, Optional, List
import ollama

DEFAULT_OLLAMA_MODEL = os.getenv("PACE_OLLAMA_MODEL", "llama3.2:1b")


def get_available_ollama_model(preferred: str = DEFAULT_OLLAMA_MODEL) -> Optional[str]:
    """Returns the matching or first available Ollama model tag, or None if Ollama is unreachable."""
    try:
        models_response = ollama.list()
        models_list = (
            models_response.get("models", [])
            if isinstance(models_response, dict)
            else getattr(models_response, "models", [])
        )
        if not models_list:
            return None
        names = []
        for m in models_list:
            name = m.get("name", "") if isinstance(m, dict) else getattr(m, "model", "")
            if name:
                names.append(name)
        # Check preferred match
        for name in names:
            if preferred in name or name in preferred:
                return name
        # If preferred not found, return the first available model
        if names:
            return names[0]
    except Exception:
        pass
    return None


def is_ollama_available(model: str = DEFAULT_OLLAMA_MODEL) -> bool:
    """Checks if Ollama is running and any model or the specified model is available."""
    return get_available_ollama_model(model) is not None


def query_ollama_stream(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
) -> Generator[str, None, None]:
    """Streams individual text tokens from Ollama chat."""
    active_model = model or get_available_ollama_model() or DEFAULT_OLLAMA_MODEL
    try:
        response = ollama.chat(model=active_model, messages=messages, stream=True)
        for chunk in response:
            content = ""
            if isinstance(chunk, dict):
                content = chunk.get("message", {}).get("content", "")
            else:
                msg = getattr(chunk, "message", None)
                if msg:
                    content = getattr(msg, "content", "")
            if content:
                yield content
    except Exception as e:
        yield f"\n[Ollama Connection Error: {e}]"


def query_ollama_text(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
) -> str:
    """Gets a full text completion from Ollama."""
    active_model = model or get_available_ollama_model() or DEFAULT_OLLAMA_MODEL
    try:
        response = ollama.chat(model=active_model, messages=messages, stream=False)
        if isinstance(response, dict):
            return response.get("message", {}).get("content", "")
        else:
            msg = getattr(response, "message", None)
            if msg:
                return getattr(msg, "content", "")
        return ""
    except Exception as e:
        return f"[Ollama Error: {e}]"


def stream_ollama_completion(
    prompt: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Streams tokens from Ollama in PACE event stream format.
    Yields events with {"type": "status"|"token", "content": "..."}.
    """
    active_model = model or get_available_ollama_model() or DEFAULT_OLLAMA_MODEL
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    yield {"type": "status", "content": f"Streaming with local Ollama ({active_model})..."}

    try:
        for token in query_ollama_stream(messages=messages, model=active_model):
            yield {"type": "token", "content": token}
        yield {"type": "status", "content": "Ollama generation complete."}
    except Exception as e:
        yield {"type": "status", "content": f"Ollama error: {e}"}
