"""Selected packaged-backend security tests; no Tauri or Windows required."""
import importlib.util
import os
from pathlib import Path
import tempfile
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / 'desktop' / 'backend_entry.py'
spec = importlib.util.spec_from_file_location('pace_desktop_entry', MODULE_PATH)
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)

def test_invalid_environment_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv('PACE_DESKTOP_PORT', '1234')
    monkeypatch.setenv('PACE_DESKTOP_KEY', 'not-a-valid-key')
    monkeypatch.setenv('PACE_DESKTOP_DATA_DIR', str(tmp_path))
    with pytest.raises(RuntimeError):
        desktop.configure()

def test_local_configuration_does_not_read_hosted_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv('PACE_DESKTOP_PORT', '12345')
    monkeypatch.setenv('PACE_DESKTOP_KEY', 'a' * 64)
    monkeypatch.setenv('PACE_DESKTOP_DATA_DIR', str(tmp_path))
    monkeypatch.setenv('AI_PROVIDER', 'huggingface')
    monkeypatch.setenv('SANDBOX_ENABLED', 'true')
    port, key = desktop.configure()
    assert port == 12345 and key == 'a' * 64
    assert os.environ['AI_PROVIDER'] == 'ollama'
    assert os.environ['SANDBOX_ENABLED'] == 'false'
    assert os.environ['DATABASE_URL'].startswith('sqlite:///')
    assert (tmp_path / 'uploads').is_dir()
