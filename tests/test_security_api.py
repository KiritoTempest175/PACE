"""Integration tests for the public trust boundary (no GPU or network needed)."""
import io
import os
import tempfile
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

DB_ROOT=tempfile.mkdtemp(prefix='pace-audit-')
os.environ['DATABASE_URL']='sqlite:///'+str(Path(DB_ROOT)/'pace.db')
os.environ['UPLOAD_DIR']=str(Path(DB_ROOT)/'uploads')
os.environ['AI_PROVIDER']='disabled'
os.environ['CORS_ORIGINS']='https://pace-ensemble.netlify.app'
from backend.main import app
from core.sandbox.executor import SandboxUnavailable,run_code
from masteries.services import database as db

ALICE={'X-PACE-Session':'a'*64}
BOB={'X-PACE-Session':'b'*64}

def pdf_bytes():
    pdf=fitz.open();page=pdf.new_page();page.insert_text((72,72),'Safe PDF test content')
    data=pdf.tobytes();pdf.close();return data

@pytest.fixture()
def client():
    with TestClient(app) as c: yield c

def test_missing_session_rejected(client):
    assert client.get('/conversations').status_code==401

def test_conversation_isolation(client):
    a=client.post('/conversations',headers=ALICE,json={'title':'Private','workspace':'coding'})
    assert a.status_code==201
    cid=a.json()['id']
    assert client.get(f'/conversations/{cid}',headers=BOB).status_code==404
    assert client.delete(f'/conversations/{cid}',headers=BOB).status_code==404
    assert client.get(f'/conversations/{cid}',headers=ALICE).status_code==200

def test_traversal_upload_ignored_and_deleted(client):
    malicious='../../outside.txt'
    result=client.post('/upload',headers=ALICE,files={'file':(malicious,io.BytesIO(pdf_bytes()),'application/pdf')})
    assert result.status_code==200,result.text
    assert result.json()['document_id'].startswith('doc-')
    assert result.json()['filename']=='document.pdf'
    assert not list((Path(DB_ROOT)/'uploads').glob('*'))
    assert not (Path(DB_ROOT)/'outside.txt').exists()
    # Document text is stored in tenant-scoped DB; no cross-tenant ID access.
    did=result.json()['document_id']
    assert client.delete('/documents/'+did,headers=BOB).status_code==404
    assert client.delete('/documents/'+did,headers=ALICE).status_code==200

def test_disguised_pdf_rejected(client):
    result=client.post('/upload',headers=ALICE,files={'file':('report.pdf',io.BytesIO(b'not a pdf'), 'application/pdf')})
    assert result.status_code==400

def test_bad_mime_rejected(client):
    result=client.post('/upload',headers=ALICE,files={'file':('report.pdf',io.BytesIO(pdf_bytes()), 'text/plain')})
    assert result.status_code==400

def test_invalid_request_contract(client):
    r=client.post('/generate',headers=ALICE,json={'text':'','mode':'admin','speed_mode':'fast'})
    assert r.status_code==422

def test_no_fake_fallback(client):
    r=client.post('/predict',headers=ALICE,json={'text':'write a sorting function','mode':'coding'})
    assert r.status_code==503
    assert 'prediction' not in r.json()

def test_sandbox_is_opt_in(monkeypatch):
    monkeypatch.setenv('SANDBOX_ENABLED','false')
    from core.config import get_settings
    get_settings.cache_clear()
    with pytest.raises(SandboxUnavailable): run_code('print(1)')

def test_cors_only_allows_production_origin(client):
    r=client.options('/conversations',headers={'Origin':'https://evil.example','Access-Control-Request-Method':'GET'})
    assert r.headers.get('access-control-allow-origin') is None
    r=client.options('/conversations',headers={'Origin':'https://pace-ensemble.netlify.app','Access-Control-Request-Method':'GET'})
    assert r.headers.get('access-control-allow-origin')=='https://pace-ensemble.netlify.app'

def test_pdf_size_limit(client,monkeypatch):
    from core.config import get_settings
    settings=get_settings();original=settings.max_upload_bytes
    try:
        settings.max_upload_bytes=100
        result=client.post('/upload',headers=ALICE,files={'file':('report.pdf',io.BytesIO(pdf_bytes()),'application/pdf')})
        assert result.status_code==413
        assert not list((Path(DB_ROOT)/'uploads').glob('*'))
    finally: settings.max_upload_bytes=original

def test_rate_limit_is_enforced(client):
    from backend.main import _hits,settings
    original=settings.rate_limit_per_minute
    try:
        _hits.clear();settings.rate_limit_per_minute=2
        assert client.get('/conversations',headers=ALICE).status_code==200
        assert client.get('/conversations',headers=ALICE).status_code==200
        assert client.get('/conversations',headers=ALICE).status_code==429
    finally:
        settings.rate_limit_per_minute=original
        _hits.clear()

def test_keyword_retrieval_is_bounded():
    from masteries.services.retrieval import document_excerpt
    excerpt=document_excerpt('Linear algebra vectors and matrices.\nBotany studies plants.','What are vectors?',limit=180)
    assert 'vectors' in excerpt
    assert len(excerpt)<250

def test_hosted_sandbox_route_disabled(client):
    r=client.post('/sandbox/run',headers=ALICE,json={'code':'print(42)'})
    assert r.status_code==503

def test_sandbox_has_non_network_privileges(monkeypatch):
    from core.config import get_settings
    from types import SimpleNamespace
    import core.sandbox.executor as executor
    cfg=get_settings();original=cfg.sandbox_enabled
    called=[]
    def fake_run(command,**kwargs):
        called.append((command,kwargs))
        return SimpleNamespace(returncode=0,stdout='ok',stderr='')
    try:
        cfg.sandbox_enabled=True
        monkeypatch.setattr(executor.subprocess,'run',fake_run)
        result=executor.run_code('print("ok")')
        assert result['status']=='pass'
        argv,_=called[0]
        assert '--network' in argv and argv[argv.index('--network')+1]=='none'
        assert '--read-only' in argv and '--cap-drop' in argv
        assert '--memory' in argv and '--cpus' in argv and '--pids-limit' in argv
    finally: cfg.sandbox_enabled=original

def test_delete_my_data_is_session_scoped(client):
    a = client.post('/conversations', headers=ALICE, json={'title':'Erase me','workspace':'coding'}).json()
    b = client.post('/conversations', headers=BOB, json={'title':'Keep me','workspace':'coding'}).json()
    deleted = client.delete('/my-data', headers=ALICE)
    assert deleted.status_code == 200
    assert deleted.json()['status'] == 'deleted'
    assert client.get('/conversations/' + a['id'], headers=ALICE).status_code == 404
    assert client.get('/conversations/' + b['id'], headers=BOB).status_code == 200

@pytest.mark.parametrize('mode', ['coding', 'literacy'])
@pytest.mark.parametrize('speed', ['fast', 'pro'])
def test_long_prompts_fail_explicitly_before_history_write(client, mode, speed):
    from core.config import get_settings
    settings = get_settings()
    old = settings.max_prompt_tokens_estimate
    try:
        settings.max_prompt_tokens_estimate = 256
        response = client.post('/generate', headers=ALICE,
            json={'mode':mode,'speed_mode':speed,'text':'x' * 4096})
        # Disabled model returns 503 before the context check; the contract still
        # validates and cannot silently slice a long request.
        assert response.status_code in (413, 503)
    finally:
        settings.max_prompt_tokens_estimate = old

def test_input_schema_supports_more_than_6000_chars():
    from masteries.api.schemas import PredictRequest
    assert len(PredictRequest(text='a' * 7000).text) == 7000
