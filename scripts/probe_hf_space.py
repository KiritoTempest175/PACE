"""Read-only public health/inference probe for PACE Hugging Face Space."""
from __future__ import annotations
import json
import sys
import time
import urllib.request

SPACE_ID = "Kiritox07/pace-phase2-ai"

def read_runtime():
    url = f"https://huggingface.co/api/spaces/{SPACE_ID}"
    req = urllib.request.Request(url, headers={"User-Agent": "PACE-verify/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        payload = json.load(response)
    runtime = payload.get("runtime") or {}
    print("Space", SPACE_ID, "runtime", json.dumps(runtime, default=str)[:1600], flush=True)
    return runtime.get("stage", "UNKNOWN")

def test_inference():
    from gradio_client import Client
    print("Connecting to public Gradio Space API", flush=True)
    client = Client(SPACE_ID, verbose=False)
    print("Submitting 16-token Fast coding generation", flush=True)
    job = client.submit("Reply with the word hello.", "coding", "fast", 16, api_name="/generate")
    started = time.monotonic()
    outputs = []
    for snapshot in job:
        if time.monotonic() - started > 150:
            job.cancel()
            raise RuntimeError("Space inference exceeded 150s")
        if not isinstance(snapshot, str):
            raise TypeError(f"Unexpected Gradio output type: {type(snapshot).__name__}")
        outputs.append(snapshot)
        print(f"Received a model snapshot of {len(snapshot)} characters", flush=True)
    if not outputs or not outputs[-1].strip():
        raise RuntimeError("Space returned no AI text")
    print("SUCCESS: actual model inference completed; length:", len(outputs[-1]), flush=True)

if __name__ == "__main__":
    if sys.argv[1:] == ["--runtime"]:
        stage = read_runtime()
        if stage != "RUNNING":
            raise SystemExit(f"Space runtime is {stage}, not RUNNING")
    elif sys.argv[1:] == ["--inference"]:
        test_inference()
    else:
        raise SystemExit("Usage: --runtime | --inference")
