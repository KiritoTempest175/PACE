"""Tests for GitHub Actions deployment, without any real Hub calls."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts import deploy_hf_space


def test_space_publishing_uses_zerogpu_and_root_files(monkeypatch):
    values = {}

    class FakeHfApi:
        def __init__(self, token):
            values["token"] = token

        def whoami(self):
            return {"name": "Kiritox07"}

        def create_repo(self, **kwargs):
            values["created"] = kwargs

        def upload_folder(self, **kwargs):
            values["uploaded"] = kwargs
            folder = Path(kwargs["folder_path"])
            values["files"] = sorted(p.name for p in folder.iterdir())
            values["readme"] = (folder / "README.md").read_text(encoding="utf-8")

    monkeypatch.setenv("HF_TOKEN", "hf_test_dummy_never_real")
    monkeypatch.setattr(deploy_hf_space, "HfApi", FakeHfApi)
    repo_id = deploy_hf_space.publish()
    assert repo_id == "Kiritox07/pace-phase2-ai"
    assert values["created"]["space_hardware"] == "zero-a10g"
    assert values["created"]["private"] is False
    assert values["created"]["repo_type"] == "space"
    assert values["files"] == ["README.md", "app.py", "requirements.txt"]
    assert "sdk: gradio\nhardware: zero-a10g\n" in values["readme"]
    assert values["uploaded"]["repo_type"] == "space"


def test_no_secret_does_not_call_hf(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="HF_TOKEN"):
        deploy_hf_space.publish()


def test_refuses_wrong_hf_account(monkeypatch):
    class FakeHfApi:
        def __init__(self, token):
            pass

        def whoami(self):
            return {"name": "WrongAccount"}

    monkeypatch.setenv("HF_TOKEN", "hf_test_dummy_never_real")
    monkeypatch.setattr(deploy_hf_space, "HfApi", FakeHfApi)
    with pytest.raises(RuntimeError, match="expected account"):
        deploy_hf_space.publish()
