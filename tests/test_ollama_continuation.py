"""Fast/Pro local provider pass counts and safe continuation boundaries."""
import pytest
from masteries.services import ollama_provider
from core.config import get_settings

@pytest.mark.parametrize("mode", ["coding", "literacy"])
def test_length_finish_triggers_continuation(monkeypatch, mode):
    calls = []
    def fake_request(prompt, selected_mode):
        calls.append((prompt,selected_mode))
        if len(calls) == 1:
            yield "first "
            return "length"
        yield "second"
        return "stop"
    monkeypatch.setattr(ollama_provider, "_request", fake_request)
    assert "".join(ollama_provider.stream_ollama("question", mode, "fast")) == "first second"
    assert len(calls) == 2

@pytest.mark.parametrize("mode", ["coding", "literacy"])
def test_pro_executes_second_review_pass(monkeypatch, mode):
    calls = []
    def fake_request(prompt, selected_mode):
        calls.append(prompt)
        yield "reviewed" if "DRAFT:" in prompt else "draft"
        return "stop"
    monkeypatch.setattr(ollama_provider, "_request", fake_request)
    assert "".join(ollama_provider.stream_ollama("question", mode, "pro")) == "reviewed"
    assert len(calls) == 2

def test_overlap_stitches_without_repeating():
    assert ollama_provider._overlap("hello world", "world again") == 5

def test_unfinished_code_triggers_followup(monkeypatch):
    calls = []
    def fake_request(prompt, mode):
        calls.append(prompt)
        if len(calls)==1:
            yield "```python\\nprint(1)"
            return "stop"
        yield "\\n```"
        return "stop"
    monkeypatch.setattr(ollama_provider, "_request", fake_request)
    text = "".join(ollama_provider.stream_ollama("Write code","coding","fast"))
    assert text.count("```") == 2
    assert len(calls) == 2
