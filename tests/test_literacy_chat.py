"""Literacy accepts ordinary conversation without an attached PDF."""
import json
from fastapi.testclient import TestClient
from backend.main import app
from core.config import get_settings

HEADERS={'X-PACE-Session':'f'*64}

def test_literacy_greeting_stays_in_literacy(monkeypatch):
    settings=get_settings()
    previous=settings.ai_provider
    settings.ai_provider='local'
    captured={}
    def fake_stream(prompt,mode,speed):
        captured.update(prompt=prompt,mode=mode,speed=speed)
        yield 'Hello. What would you like to discuss?'
    monkeypatch.setattr('masteries.api.router.stream_generate',fake_stream)
    try:
        with TestClient(app) as client:
            response=client.post('/generate',headers=HEADERS,json={'text':'hello','mode':'literacy','speed_mode':'fast'})
            assert response.status_code==200,response.text
            events=[json.loads(line[5:]) for line in response.text.splitlines() if line.startswith('data: ')]
            assert events[-1]['type']=='done'
            assert captured['mode']=='literacy'
            assert 'USER: hello' in captured['prompt']
            assert 'Do not produce source code' in captured['prompt']
    finally:
        settings.ai_provider=previous
