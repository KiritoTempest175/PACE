"""
PACE Actor Inference Node
Task LE-1: Loads the trained Actor Model, generates multiple code fixes based on a prompt.
"""

import torch
import gc
from transformers import AutoTokenizer, AutoModelForCausalLM


def generate_fixes(
    prompt: str,
    model_dir: str = "masteries/coding/models/actor_v1",
    num_return_sequences: int = 3,
) -> list[str]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    tokenizer.pad_token = tokenizer.eos_token

    # Load the custom 164M fine-tuned Actor
    model = AutoModelForCausalLM.from_pretrained(model_dir).to(device)

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
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            num_return_sequences=num_return_sequences,
        )

    decoded_texts = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

    # VRAM PURGE: Destroy tensors and clear cache
    del model, tokenizer, inputs, generated_ids
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
        print(
            f"[VRAM] Actor Purged. Idling Footprint: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
        )

    return decoded_texts


if __name__ == "__main__":
    print("[SYSTEM] Testing Actor Inference Engine...")
    test_prompt = "def calculate_sum(a, b):"
    print(generate_fixes(test_prompt, num_return_sequences=1))
