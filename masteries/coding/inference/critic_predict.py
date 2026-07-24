"""
PACE Critic Inference Node
Task LE-2: Loads the trained micro-model, evaluates a code string, and returns 0 or 1.
"""

import torch
import gc
from transformers import AutoTokenizer, AutoModelForSequenceClassification


def evaluate_syntax(
    code_snippet: str, model_dir: str = "masteries/coding/artifacts/critic_v1"
) -> int:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(device)
    inputs = tokenizer(
        code_snippet,
        truncation=True,
        max_length=512,
        padding="max_length",
        return_tensors="pt",
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    logits = logits.argmax(dim=-1)
    del model, tokenizer, inputs, outputs
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
        print(
            f"[VRAM] Pipeline Purged. Idling Context Footprint: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
        )
    return logits.item()


if __name__ == "__main__":
    print("[SYSTEM] Testing Critic Inference Engine...")

    bad_code = """
    def calculate_sum(a, b)
    return a + b
    """

    print("Testing Critic Inference Engine...")
    print(evaluate_syntax(bad_code))
