"""Literacy accepts ordinary chat without PDF and does not silently select Coding."""
import json

from fastapi.testclient import TestClient
from backend.main import app
from core.config import get_settings

HEADERS = {'X-PACE-Session': 'e' * 64}


def test_plain_literacy_greeting_without_pdf(monkeypatch):
    settings = get_settings()
    previous = settings.ai_provider
    settings.ai_provider = 'local'
    captured = {}

    def fake_stream(prompt, mode, speed):
        captured.update(prompt=prompt, mode=mode, speed=speed)
        yield 'Hello! How can I help?'

    monkeypatch.setattr('masteries.api.router.stream_generate', fake_stream)
    try:
        with TestClient(app) as client:
            response = client.post('/generate', headers=HEADERS, json={
                'text': 'hello', 'mode': 'literacy', 'speed_mode': 'fast'
            })
            assert response.status_code == 200, response.text
            events = [json.loads(line[5:]) for line in response.text.splitlines()
                      if line.startswith('data: ')]
            assert events[-1]['type'] == 'done'
            assert captured['mode'] == 'literacy'
            assert 'USER: hello' in captured['prompt']
            assert 'Do not produce source code' in captured['prompt']
            conversation = client.get('/conversations/' + events[0]['conversation_id'],
                                      headers=HEADERS).json()
            assert conversation['workspace'] == 'literacy'
    finally:
        settings.ai_provider = previous
