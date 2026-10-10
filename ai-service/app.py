"""PACE hosted inference on Hugging Face Gradio ZeroGPU.

A single small pretrained model is used. Fast mode streams real decoded tokens.
Review mode performs a second pass with the *same* model and sends only the
final revision, which must never be described as independent critic approval.
Model weights are loaded at module import and moved to CUDA before GPU calls,
as prescribed by current ZeroGPU's CUDA-emulation initialization contract.
"""
from __future__ import annotations

import os
from threading import Thread, Lock
from typing import Iterator

import spaces  # Import before torch: ZeroGPU CUDA emulation applies during startup.
import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

MODEL_ID = os.getenv("PACE_MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TOKENIZER = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=False)
MODEL = AutoModelForCausalLM.from_pretrained(MODEL_ID, trust_remote_code=False)
MODEL = MODEL.to(DEVICE)
MODEL.eval()


SYSTEM_PROMPTS = {
    "coding": "Give clear, correct programming advice. Never claim code was executed or tested.",
    "literacy": "Answer only from the provided excerpts. Say clearly when information is missing.",
    "research": "Explain carefully. Do not invent sources or claim web research was performed.",
}


def prompt_for(text: str, mode: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[mode]},
        {"role": "user", "content": text},
    ]
    return TOKENIZER.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def _model_tokens(text: str, mode: str, budget: int) -> Iterator[str]:
    """Stream from the actual model, surfacing background worker exceptions."""
    inputs = TOKENIZER(
        prompt_for(text, mode),
        return_tensors="pt",
        truncation=True,
        max_length=3072,
    ).to(DEVICE)
    streamer = TextIteratorStreamer(
        TOKENIZER, skip_prompt=True, skip_special_tokens=True, timeout=5,
    )
    failures: list[Exception] = []

    def run_model():
        try:
            with torch.inference_mode():
                MODEL.generate(
                    **inputs, max_new_tokens=budget, do_sample=False,
                    pad_token_id=TOKENIZER.eos_token_id, streamer=streamer,
                )
        except Exception as exc:
            failures.append(exc)
            # Wake the stream consumer instead of hanging on an empty queue.
            streamer.on_finalized_text("", stream_end=True)

    thread = Thread(target=run_model, daemon=True)
    thread.start()
    try:
        for piece in streamer:
            if piece:
                yield piece
    finally:
        thread.join(timeout=2)
    if failures:
        raise gr.Error("The AI model failed to generate a response") from failures[0]


# CPU execution is intentionally separate from the ZeroGPU-decorated function.
# It supplies real model output if Hugging Face rejects a GPU quota/job.
_CPU_MODEL = None
_CPU_LOCK = Lock()


def _cpu_model():
    global _CPU_MODEL
    with _CPU_LOCK:
        if _CPU_MODEL is None:
            model = AutoModelForCausalLM.from_pretrained(MODEL_ID, trust_remote_code=False)
            _CPU_MODEL = model.to("cpu").eval()
    return _CPU_MODEL


def _cpu_tokens(text: str, mode: str, budget: int) -> Iterator[str]:
    model = _cpu_model()
    inputs = TOKENIZER(
        prompt_for(text, mode), return_tensors="pt", truncation=True, max_length=2048,
    ).to("cpu")
    streamer = TextIteratorStreamer(
        TOKENIZER, skip_prompt=True, skip_special_tokens=True, timeout=45,
    )
    failures: list[Exception] = []

    def run_model():
        try:
            with torch.inference_mode():
                model.generate(**inputs, max_new_tokens=min(128, budget),
                               do_sample=False, pad_token_id=TOKENIZER.eos_token_id,
                               streamer=streamer)
        except Exception as exc:
            failures.append(exc)
            streamer.on_finalized_text("", stream_end=True)

    thread = Thread(target=run_model, daemon=True)
    thread.start()
    try:
        for piece in streamer:
            if piece:
                yield piece
    finally:
        thread.join(timeout=2)
    if failures:
        raise gr.Error("CPU model failed to generate a response") from failures[0]


def generate_cpu(text: str, mode: str, speed: str, max_new_tokens: int) -> Iterator[str]:
    """Real CPU fallback with no ZeroGPU allocation or user quota dependency."""
    if mode not in SYSTEM_PROMPTS or speed not in {"fast", "pro"}:
        raise gr.Error("Unsupported workspace or generation mode")
    if not isinstance(text, str) or not 1 <= len(text) <= 12000:
        raise gr.Error("Invalid prompt length")
    if not isinstance(max_new_tokens, int) or not 16 <= max_new_tokens <= 256:
        raise gr.Error("Invalid token budget")
    snapshot = ""
    for piece in _cpu_tokens(text, mode, max_new_tokens):
        snapshot += piece
        if speed == "fast":
            yield snapshot
    if not snapshot.strip():
        raise gr.Error("CPU model returned no response")
    if speed == "pro":
        prompt = (
            "Review this draft for errors and return the corrected answer only. "
            "Be explicit when uncertain.\\nQUESTION:\\n" + text[:3000]
            + "\\nDRAFT:\\n" + snapshot[:3000]
        )
        revised = "".join(_cpu_tokens(prompt, mode, max_new_tokens)).strip()
        if not revised:
            raise gr.Error("CPU review failed")
        yield revised

def duration_for(text: str, mode: str, speed: str, max_new_tokens: int) -> int:
    # Sized conservatively for a 0.5B model; benchmark representative requests
    # and tune for the actual Space hardware/visitor GPU quota.
    return 55 if speed == "pro" else 35


@spaces.GPU(duration=duration_for)
def generate(text: str, mode: str, speed: str, max_new_tokens: int) -> Iterator[str]:
    if mode not in SYSTEM_PROMPTS or speed not in {"fast", "pro"}:
        raise gr.Error("Unsupported workspace or generation mode")
    if not isinstance(text, str) or not 1 <= len(text) <= 12000:
        raise gr.Error("Invalid prompt length")
    if not isinstance(max_new_tokens, int) or not 16 <= max_new_tokens <= 256:
        raise gr.Error("Invalid token budget")

    snapshot = ""
    for piece in _model_tokens(text, mode, max_new_tokens):
        snapshot += piece
        if speed == "fast":
            yield snapshot
    if not snapshot.strip():
        raise gr.Error("The AI model returned no response")

    if speed == "pro":
        critique_prompt = (
            "Review the answer for mistakes. Return the corrected answer only. "
            "If facts cannot be verified, state the uncertainty.\n\n"
            "QUESTION:\n" + text[:5000] + "\n\nDRAFT:\n" + snapshot[:5000]
        )
        revision = "".join(_model_tokens(critique_prompt, mode, max_new_tokens)).strip()
        if not revision:
            raise gr.Error("Review was incomplete")
        yield revision


with gr.Blocks(title="PACE AI Service") as demo:
    gr.Markdown("# PACE AI Service\nSingle-model inference, not an independent actor-critic ensemble.")
    with gr.Row():
        prompt = gr.Textbox(label="Prompt", lines=4)
        mode = gr.Dropdown(list(SYSTEM_PROMPTS), value="coding", label="Workspace")
        speed = gr.Dropdown(["fast", "pro"], value="fast", label="Generation mode")
        budget = gr.Slider(16, 256, value=128, step=16, label="Max output tokens")
    response = gr.Textbox(label="Model response", lines=12)
    gr.Button("Generate").click(
        generate, [prompt, mode, speed, budget], response,
        api_name="generate", concurrency_limit=1,
    )

    with gr.Accordion("CPU fallback (for ZeroGPU quota limits)", open=False):
        gr.Markdown("Uses the same pretrained model on CPU; slower, not a fake response.")
        cpu_output = gr.Textbox(label="CPU model response", lines=10)
        gr.Button("Generate on CPU").click(
            generate_cpu, [prompt, mode, speed, budget], cpu_output,
            api_name="generate_cpu", concurrency_limit=1,
        )

demo.queue(max_size=12, default_concurrency_limit=1)
if __name__ == "__main__":
    demo.launch()
