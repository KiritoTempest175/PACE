"""Publish the existing PACE AI service to a dedicated Hugging Face ZeroGPU Space.

Invoked only by workflow_dispatch. Never log the HF_TOKEN value or put it
in Space source files. Requires a Hugging Face token with repo write access.
Fails closed if ZeroGPU hosting is not available (no paid hardware fallback).
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

EXPECTED_OWNER = "Kiritox07"
SPACE_NAME = "pace-phase2-ai"
HARDWARE = "zero-a10g"
SOURCE = Path(__file__).resolve().parents[1] / "ai-service"
SPACE_FILES = ("app.py", "requirements.txt", "README.md")


def publish() -> str:
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        raise RuntimeError("HF_TOKEN GitHub Actions secret is not configured.")

    requested_name = os.environ.get("PACE_SPACE_NAME", SPACE_NAME).strip()
    if requested_name != SPACE_NAME or not re.fullmatch(r"[a-z0-9-]+", requested_name):
        raise RuntimeError("This workflow only deploys to the dedicated Phase 2 Space.")

    api = HfApi(token=token)
    owner = api.whoami()["name"]
    if owner != EXPECTED_OWNER:
        raise RuntimeError(
            "Authenticated Hugging Face token does not belong to the expected account."
        )
    repo_id = f"{owner}/{requested_name}"

    for filename in SPACE_FILES:
        if not (SOURCE / filename).is_file():
            raise FileNotFoundError(f"Required Space source missing: {filename}")

    # Creating explicitly on ZeroGPU avoids accidentally assigning paid hardware.
    # If the Free account does not qualify, the API rejects this request.
    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="gradio",
        space_hardware=HARDWARE,
        private=False,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory(prefix="pace-space-") as tmp:
        root = Path(tmp)
        for filename in SPACE_FILES:
            (root / filename).write_bytes((SOURCE / filename).read_bytes())

        # The Space needs its README at the repository root, not ai-service/.
        readme = root / "README.md"
        contents = readme.read_text(encoding="utf-8")
        if "sdk: gradio" not in contents:
            raise RuntimeError("Space README is missing its Gradio metadata.")
        if "hardware: " not in contents:
            contents = contents.replace(
                "sdk: gradio", f"sdk: gradio\\nhardware: {HARDWARE}", 1
            )
        readme.write_text(contents, encoding="utf-8")

        api.upload_folder(
            folder_path=str(root),
            repo_id=repo_id,
            repo_type="space",
            commit_message="Deploy PACE Phase 2 hosted inference",
        )

    print(f"Uploaded app.py, requirements.txt, README.md to https://huggingface.co/spaces/{repo_id}")
    print("Build and inference must be checked on Hugging Face before enabling Render AI.")
    return repo_id


if __name__ == "__main__":
    publish()
