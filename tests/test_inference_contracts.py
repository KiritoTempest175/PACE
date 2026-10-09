"""The streaming and model-failure contracts cannot claim success by accident."""
import json

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from core.config import get_settings
from masteries.services import ai_gateway

HEADERS = {"X-PACE-Session": "d" * 64}
REQUEST = {"text": "Explain binary search", "mode": "coding", "speed_mode": "fast"}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _events(response):
    return [json.loads(line[5:]) for line in response.text.splitlines() if line.startswith("data: ")]


def test_preflight_returns_503_without_ai(client):
    assert client.post("/generate", headers=HEADERS, json=REQUEST).status_code == 503


def test_streams_real_chunks_and_persists_only_on_done(client, monkeypatch):
    settings = get_settings()
    prior = settings.ai_provider
    settings.ai_provider = "local"
    monkeypatch.setattr("masteries.api.router.stream_generate", lambda *args: iter(["Binary ", "search"] ))
    try:
        r = client.post("/generate", headers=HEADERS, json=REQUEST)
        assert r.status_code == 200, r.text
        events = _events(r)
        assert [e["type"] for e in events] == ["init", "token", "token", "done"]
        assert events[1]["content"] == "Binary "
        assert events[2]["content"] == "search"
        record = client.get("/conversations/" + events[0]["conversation_id"], headers=HEADERS)
        assert record.status_code == 200
        assert [m["role"] for m in record.json()["messages"]] == ["user", "assistant"]
        assert record.json()["messages"][1]["text"] == "Binary search"
    finally:
        settings.ai_provider = prior


def test_stream_failure_never_persists_fake_assistant(client, monkeypatch):
    settings = get_settings()
    prior = settings.ai_provider
    settings.ai_provider = "local"

    def interrupted(*args):
        yield "partial output"
        raise ai_gateway.AIUnavailable("secret provider error")

    monkeypatch.setattr("masteries.api.router.stream_generate", interrupted)
    try:
        r = client.post("/generate", headers=HEADERS, json=REQUEST)
        assert r.status_code == 200  # Stream already started; error is a frame.
        events = _events(r)
        assert events[-1] == {"type": "error", "content": "AI inference unavailable or quota exhausted"}
        assert "done" not in [e["type"] for e in events]
        assert "secret" not in r.text
        record = client.get("/conversations/" + events[0]["conversation_id"], headers=HEADERS)
        assert [m["role"] for m in record.json()["messages"]] == ["user"]
    finally:
        settings.ai_provider = prior


def test_local_ensemble_has_no_fake_fallback(monkeypatch):
    from masteries.services import local_ensemble

    class Actor:
        def generate_code(self, text):
            yield "actual output"
        def revise_code(self, text, initial, critique):
            yield "revised output"

    class Critic:
        def critique(self, text, context):
            yield "actual critique"

    monkeypatch.setattr(local_ensemble, "_actor", lambda mode: Actor())
    monkeypatch.setattr(local_ensemble, "_critic", lambda mode: Critic())
    assert "".join(local_ensemble.stream_local_ensemble("topic", "coding", "fast")) == "actual output"
    assert "".join(local_ensemble.stream_local_ensemble("topic", "coding", "pro")) == "revised output"
    class EmptyCritic:
        def critique(self, *args, **kwargs):
            return iter([])
    monkeypatch.setattr(local_ensemble, "_critic", lambda mode: EmptyCritic())
    with pytest.raises(ai_gateway.AIUnavailable):
        "".join(local_ensemble.stream_local_ensemble("topic", "coding", "pro"))


def test_invalid_conversation_workspace_rejected(client, monkeypatch):
    settings = get_settings()
    prior = settings.ai_provider
    settings.ai_provider = "local"
    try:
        created = client.post("/conversations", headers=HEADERS,
                              json={"title": "Coding", "workspace": "coding"})
        assert created.status_code == 201
        payload = {**REQUEST, "conversation_id": created.json()["id"], "mode": "research"}
        assert client.post("/generate", headers=HEADERS, json=payload).status_code == 422
    finally:
        settings.ai_provider = prior


def test_model_snapshot_adapter(monkeypatch):
    from masteries.services.ai_gateway import _huggingface_stream
    class FakeJob:
        def __init__(self): self.cancelled = False
        def __iter__(self): return iter(["He", "Hello", "Hello world"])
        def done(self): return True
        def cancel(self): self.cancelled = True
    class FakeClient:
        def submit(self, *args, **kwargs): return FakeJob()
    monkeypatch.setattr(ai_gateway, "_hf_client", lambda *args: FakeClient())
    settings = get_settings()
    previous_space = settings.hf_space_id
    settings.hf_space_id = "org/pace"
    try:
        assert list(_huggingface_stream("prompt", "coding", "fast")) == ["He", "llo", " world"]
    finally:
        settings.hf_space_id = previous_space


def test_ingress_413_for_oversized_declared_body(client):
    # Pre-multipart transport limit, not just PDF payload validation.
    settings = get_settings()
    prior = settings.max_upload_bytes
    settings.max_upload_bytes = 1024
    try:
        res = client.post('/upload', headers={**HEADERS, 'Content-Length': '90000'},
                          content=b'x' * 90000)
        assert res.status_code == 413
    finally:
        settings.max_upload_bytes = prior


def test_document_context_attaches_to_literacy_conversation(client, monkeypatch):
    from masteries.services import database as db
    settings = get_settings()
    prior = settings.ai_provider
    settings.ai_provider = 'local'
    try:
        # This is an actual persisted text record, not an external PDF reference.
        from masteries.api.router import owner_for_session
        owner = owner_for_session(HEADERS['X-PACE-Session'])
        did = db.save_document(owner, 'The paper states the model is not validated.')
        monkeypatch.setattr('masteries.api.router.stream_generate',lambda *args: iter(['Model is not validated.']))
        request = {**REQUEST, 'mode': 'literacy', 'document_id': did}
        response = client.post('/generate',headers=HEADERS,json=request)
        assert response.status_code == 200
        cid = _events(response)[0]['conversation_id']
        assert client.get('/conversations/'+cid,headers=HEADERS).json()['document_id'] == did
        # A follow-up without document_id retrieves the attached, owned text.
        request.pop('document_id')
        request['conversation_id'] = cid
        assert client.post('/generate', headers=HEADERS, json=request).status_code == 200
        assert client.delete('/documents/'+did,headers=HEADERS).status_code == 200
        assert client.get('/conversations/'+cid,headers=HEADERS).json()['document_id'] is None
    finally:
        settings.ai_provider = prior
