"""
PACE Actor Inference Node
Task LE-1: Loads a Causal Language Model, generates a code fix based on a prompt, and returns the string.
"""

import torch
import gc
from transformers import AutoTokenizer, AutoModelForCausalLM


def generate_fix(
    prompt: str, model_id: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
) -> str:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch.float16
    ).to(device)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True,
        padding="max_length",
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs, max_new_tokens=256, temperature=0.2, do_sample=True
        )

    del model, tokenizer, inputs, generated_ids
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
        print(
            f"[VRAM] Pipeline Purged. Idling Context Footprint: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
        )


if __name__ == "__main__":
    print("[SYSTEM] Testing Actor Inference Engine...")

    test_prompt = "Fix this Python code:\n```python\ndef calculate_sum(a, b)\n    return a + b\n```\nCorrected code:"

    print(generate_fix(test_prompt))
