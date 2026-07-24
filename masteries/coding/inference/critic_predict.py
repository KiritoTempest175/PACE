"""
PACE Critic Inference Node
Task LE-2: Loads the trained micro-model, evaluates a code string, and returns 0 or 1.
"""

# IMPORT REQUIRED LIBRARIES HERE
# You will need torch, gc, AutoTokenizer, and AutoModelForSequenceClassification.
import torch
import gc
from transformers import AutoTokenizer, AutoModelForSequenceClassification


def evaluate_syntax(
    code_snippet: str, model_dir: str = "masteries/coding/artifacts/critic_v1"
) -> int:
    # ==========================================
    # 1. HARDWARE ROUTING
    # ==========================================
    # Check if CUDA is available, otherwise default to CPU. Define the device.
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ==========================================
    # 2. LOAD ARTIFACTS
    # ==========================================
    # Load the tokenizer from 'model_dir'.
    # Load the sequence classification model from 'model_dir'.
    # Route the model to your active compute device.
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(device)
    # ==========================================
    # 3. PREPARE INPUTS
    # ==========================================
    # Tokenize the 'code_snippet'.
    # (Requirement: Tell the tokenizer to return PyTorch tensors, truncate the text, and set max_length to 512).
    # Route the resulting 'input_ids' and 'attention_mask' to your active device.
    inputs = tokenizer(
        code_snippet,
        truncation=True,
        max_length=512,
        padding="max_length",
        return_tensors="pt",
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # ==========================================
    # 4. INFERENCE ENGINE (NO GRADIENTS)
    # ==========================================
    # Open a context manager that disables PyTorch gradient calculations (this saves massive VRAM since we aren't training).
    # Inside the context manager, pass your inputs through the model.

    with torch.no_grad():
        outputs = model(**inputs)

    # ==========================================
    # 5. EXTRACT PREDICTION
    # ==========================================
    # Extract the 'logits' tensor from the model's output.
    # Find the index of the highest probability in the logits (Hint: use argmax).
    # Convert that single tensor value into a standard Python integer.
    logits = outputs.logits
    logits = logits.argmax(dim=-1)

    # ==========================================
    # 6. VRAM TEARDOWN PROTOCOL
    # ==========================================
    # Delete the model, tokenizer, inputs, and output tensors.
    # Force Python garbage collection.
    # If using CUDA, empty the PyTorch cache.

    del model, tokenizer, inputs, outputs
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
        print(
            f"[VRAM] Pipeline Purged. Idling Context Footprint: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
        )

    # ==========================================
    # 7. RETURN
    # ==========================================
    # Return the final integer prediction.
    return logits.item()


# =====================================================================
# SYSTEM TEST ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    print("[SYSTEM] Testing Critic Inference Engine...")

    # Write a snippet of Python code with an intentional missing colon
    bad_code = """
    def calculate_sum(a, b)
    return a + b
    """

    # Call your evaluate_syntax function and print the result.
    # Expected output: 1 (Bug detected)

    print("Testing Critic Inference Engine...")
    print(evaluate_syntax(bad_code))
