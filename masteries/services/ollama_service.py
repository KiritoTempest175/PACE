"""
Ollama Service Module for PACE
Provides streaming and non-streaming completions using local Ollama models (e.g. llama3.2:1b).
"""

from typing import Generator, Dict, Any, Optional
import ollama


def is_ollama_available(model: str = "llama3.2:1b") -> bool:
    """Checks if Ollama is running and the model is available."""
    try:
        models_response = ollama.list()
        models_list = models_response.get("models", []) if isinstance(models_response, dict) else getattr(models_response, "models", [])
        for m in models_list:
            name = m.get("name", "") if isinstance(m, dict) else getattr(m, "model", "")
            if model in name or name in model:
                return True
        return False
    except Exception:
        return False


def stream_ollama_completion(
    prompt: str,
    model: str = "llama3.2:1b",
    system_prompt: Optional[str] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Streams tokens from Ollama in PACE event stream format.
    Yields events with {"type": "status"|"token", "content": "..."}.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    yield {"type": "status", "content": f"Streaming with Ollama model ({model})..."}

    try:
        response = ollama.chat(model=model, messages=messages, stream=True)
        for chunk in response:
            content = ""
            if isinstance(chunk, dict):
                content = chunk.get("message", {}).get("content", "")
            else:
                msg = getattr(chunk, "message", None)
                if msg:
                    content = getattr(msg, "content", "")
            
            if content:
                yield {"type": "token", "content": content}

        yield {"type": "status", "content": "Ollama generation complete."}

    except Exception as e:
        yield {"type": "status", "content": f"Ollama error: {e}"}
        raise e
