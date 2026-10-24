from pathlib import Path
from desktop.model_scan import scan_models

def test_local_model_discovery_bounded_and_read_only(tmp_path: Path):
    safe = tmp_path / 'models'
    safe.mkdir()
    (safe / 'model-Q4_K_M.gguf').write_bytes(b'1234')
    (safe / 'weights.safetensors').write_bytes(b'123456')
    (safe / 'notes.txt').write_text('ignore')
    results = scan_models([safe], limit=2)
    assert len(results) == 2
    assert {r['format'] for r in results} == {'gguf','safetensors'}
    assert all(r['loadable'] is False for r in results)
    assert (safe / 'model-Q4_K_M.gguf').read_bytes() == b'1234'
