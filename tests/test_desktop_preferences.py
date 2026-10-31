"""Desktop-only settings and local inference resource policies."""
from unittest.mock import patch
import pytest
from fastapi import HTTPException
from desktop import model_manager as mgr
from masteries.services import ollama_provider

@pytest.fixture()
def personal_dir(monkeypatch,tmp_path):
    monkeypatch.setenv("PACE_DESKTOP_DATA_DIR",str(tmp_path))
    return tmp_path

def test_local_preferences_persist_and_path_is_exposed(personal_dir):
    before=mgr.current_preferences()
    assert before["preferences"]["context_tokens"]==8192
    mgr.update_preferences(mgr.LocalPreferences(context_tokens=16384,temperature=0.7))
    assert mgr.read_preferences()=={"context_tokens":16384,"temperature":0.7}
    assert (personal_dir/"generation-preferences.json").is_file()

def test_local_preferences_reject_unknown_huge_context(personal_dir):
    with pytest.raises(HTTPException) as exc:
        mgr.update_preferences(mgr.LocalPreferences(context_tokens=99999999,temperature=0))
    assert exc.value.status_code==422

def test_local_model_has_no_fixed_256_token_cap(personal_dir,monkeypatch):
    monkeypatch.setattr(ollama_provider,"desktop_role_model",lambda role:"qwen2.5-coder:3b")
    requests=[]
    class Stream:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def raise_for_status(self):pass
        def iter_lines(self):
            yield '{"message":{"content":"Ready"},"done":false}'
            yield '{"done":true,"done_reason":"stop"}'
    class Client:
        def __init__(self,**k):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def stream(self,method,url,json):
            requests.append(json)
            return Stream()
    monkeypatch.setattr(ollama_provider.httpx,"Client",Client)
    assert "".join(ollama_provider.stream_ollama("Write a full program","coding","fast"))=="Ready"
    assert requests[0]["options"]["num_predict"]==-1
    assert requests[0]["options"]["num_ctx"]==8192
    assert requests[0]["options"]["temperature"]==0.2
