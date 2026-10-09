"""Model catalog, user choice, persistence and real actor/reviewer regression."""
import json
from unittest.mock import patch
import pytest
from fastapi import HTTPException
from desktop import model_manager as manager
from masteries.services import ollama_provider
from masteries.services.ai_gateway import AIUnavailable

@pytest.fixture
def data_dir(monkeypatch,tmp_path):
    monkeypatch.setenv("PACE_DESKTOP_DATA_DIR",str(tmp_path))
    return tmp_path

def test_catalog_contains_free_models_between_1b_and_8b():
    assert len(manager.CATALOG)>=8
    assert all(row["id"] in manager.ALLOWED for row in manager.CATALOG)
    assert "qwen2.5-coder:1.5b" in manager.ALLOWED
    assert "qwen3:8b" in manager.ALLOWED

def test_initial_model_selection_requires_user_action(data_dir):
    assert manager.read_selection()=={"actor":None,"critic":None}
    with pytest.raises(AIUnavailable,match="actor"):
        ollama_provider.desktop_role_model("actor")

def test_two_different_models_persist_between_runs(data_dir,monkeypatch):
    monkeypatch.setattr(manager,"installed_models",lambda:["llama3.2:1b","gemma3:4b"])
    manager.select_model(manager.ModelSelection(role="actor",model="llama3.2:1b"))
    manager.select_model(manager.ModelSelection(role="critic",model="gemma3:4b"))
    assert manager.read_selection()=={"actor":"llama3.2:1b","critic":"gemma3:4b"}
    assert ollama_provider.desktop_role_model("actor")=="llama3.2:1b"
    assert ollama_provider.desktop_role_model("critic")=="gemma3:4b"

def test_model_names_restricted_no_uninstalled_models(data_dir,monkeypatch):
    monkeypatch.setattr(manager,"installed_models",lambda:["gemma3:4b"])
    for name in ("../../tmp","qwen3:100b","bash -c rm -rf","http://attacker.example"):
        with pytest.raises(HTTPException) as exc:
            manager.select_model(manager.ModelSelection(role="critic",model=name))
        assert exc.value.status_code==422
    with pytest.raises(HTTPException) as exc:
        manager.select_model(manager.ModelSelection(role="actor",model="llama3.2:3b"))
    assert exc.value.status_code==409

def test_pro_uses_different_generator_and_reviewer_models(data_dir,monkeypatch):
    monkeypatch.setattr(manager,"read_selection",lambda:{"actor":"llama3.2:1b","critic":"gemma3:4b"})
    class FakeStream:
        def __init__(self,answer):self.answer=answer
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def raise_for_status(self):pass
        def iter_lines(self):
            yield json.dumps({"message":{"content":self.answer},"done":False})
            yield json.dumps({"done":True})
    class FakeClient:
        calls=[]
        def __init__(self,**kwargs):pass
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def stream(self,method,url,json):
            self.calls.append(json["model"])
            return FakeStream("draft" if len(self.calls)==1 else "reviewed")
    monkeypatch.setattr(ollama_provider.httpx,"Client",FakeClient)
    assert "".join(ollama_provider.stream_ollama("hello","coding","pro"))=="reviewed"
    assert FakeClient.calls==["llama3.2:1b","gemma3:4b"]

def test_fast_keeps_original_single_pass(data_dir,monkeypatch):
    monkeypatch.setattr(manager,"read_selection",lambda:{"actor":"gemma3:1b","critic":None})
    monkeypatch.setattr(ollama_provider,"_request",lambda text,mode,role="actor":iter([role]))
    assert "".join(ollama_provider.stream_ollama("hello","coding","fast"))=="actor"
    with pytest.raises(AIUnavailable,match="critic"):
        ollama_provider.desktop_role_model("critic")
