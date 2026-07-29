"""
PACE Actor Model – Test & Evaluation
Loads the fine-tuned checkpoint, evaluates accuracy / perplexity on a held-out
test split, and runs a code-generation demo with a sample prompt.
"""

import math
import torch
from torch.utils.data import DataLoader, random_split
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm

from dataset import CoderActorDataset


def evaluate(model, dataloader, device):
    """
    Runs the model over every batch in *dataloader* and returns:
        avg_loss      – mean cross-entropy loss across all batches
        perplexity    – exp(avg_loss)
        accuracy      – token-level prediction accuracy (ignoring padding / -100 labels)
    """
    model.eval()

    total_loss = 0.0
    total_correct = 0
    total_tokens = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )

            total_loss += outputs.loss.item()

            # ── Token-level accuracy ──────────────────────────────
            # Causal LM: logits are shifted so that logits[t] predicts token[t+1].
            # HuggingFace already does this shift internally for the loss,
            # but we need to do it ourselves for accuracy.
            shift_logits = outputs.logits[:, :-1, :]  # (B, T-1, V)
            shift_labels = labels[:, 1:]  # (B, T-1)

            predictions = shift_logits.argmax(dim=-1)  # (B, T-1)

            # Only count positions where the label is not -100 (padding)
            valid_mask = shift_labels != -100
            total_correct += (
                (predictions[valid_mask] == shift_labels[valid_mask]).sum().item()
            )
            total_tokens += valid_mask.sum().item()

    avg_loss = total_loss / len(dataloader)
    perplexity = math.exp(avg_loss)
    accuracy = (total_correct / total_tokens * 100) if total_tokens > 0 else 0.0

    return avg_loss, perplexity, accuracy


def generate_code(model, tokenizer, prompt, device, max_new_tokens=200):
    """
    Generates Python code from a natural-language or code *prompt*.
    Returns the decoded string (prompt + completion).
    """
    model.eval()
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            repetition_penalty=1.15,
            pad_token_id=tokenizer.eos_token_id,
        )

    return tokenizer.decode(output_ids[0], skip_special_tokens=True)


def main():
    # ==========================================
    # 1. HARDWARE SETUP
    # ==========================================
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}\n")

    # ==========================================
    # 2. LOAD FINE-TUNED MODEL & TOKENIZER
    # ==========================================
    model_dir = "masteries/coding/models/actor_v1"
    print(f"Loading fine-tuned model from: {model_dir}")

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_dir).to(device)
    print(
        f"Model loaded  –  {sum(p.numel() for p in model.parameters()):,} parameters\n"
    )

    # ==========================================
    # 3. PREPARE TEST SPLIT
    # ==========================================
    full_dataset = CoderActorDataset(
        parquet_path="masteries/coding/data/raw/stack_python_157k.parquet",
        tokenizer=tokenizer,
        max_length=512,
    )

    # Use 1 % of the data as a test set (fast but representative)
    test_size = max(1, int(len(full_dataset) * 0.01))
    _, test_dataset = random_split(
        full_dataset,
        [len(full_dataset) - test_size, test_size],
        generator=torch.Generator().manual_seed(42),
    )

    test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False)
    print(f"Test split: {len(test_dataset)} samples  ({len(test_loader)} batches)\n")

    # ==========================================
    # 4. EVALUATION – Loss / Perplexity / Accuracy
    # ==========================================
    print("=" * 60)
    print("  EVALUATION RESULTS")
    print("=" * 60)

    avg_loss, perplexity, accuracy = evaluate(model, test_loader, device)

    print(f"\n  Average Loss  : {avg_loss:.4f}")
    print(f"  Perplexity    : {perplexity:.2f}")
    print(f"  Token Accuracy: {accuracy:.2f}%\n")

    # ==========================================
    # 5. CODE GENERATION – Test Prompt
    # ==========================================
    test_prompt = "def fibonacci(n):"

    print("=" * 60)
    print("  CODE GENERATION DEMO")
    print("=" * 60)
    print(f"\n  Prompt: {test_prompt}\n")
    print("-" * 60)

    generated = generate_code(model, tokenizer, test_prompt, device)
    print(generated)
    print("-" * 60)

    print("\nTest complete.")


if __name__ == "__main__":
    main()
