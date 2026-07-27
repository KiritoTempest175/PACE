"""
PACE Critic Model – Test & Evaluation
Loads the fine-tuned checkpoint, evaluates loss and classification metrics (accuracy, precision, recall, F1)
on a held-out test split, and runs a bug-detection demo on sample code snippets.
"""

import torch
from torch.utils.data import DataLoader, random_split
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm

from dataset import CoderCriticDataset


def evaluate(model, dataloader, device):
    """
    Runs the model over every batch in *dataloader* and returns evaluation metrics:
        avg_loss  – mean cross-entropy loss across all batches
        accuracy  – classification accuracy (%)
        precision – precision for BUG detection (%)
        recall    – recall for BUG detection (%)
        f1        – F1 score for BUG detection (%)
    """
    model.eval()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    # For precision/recall/F1 (class 1 = BUG)
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch["input_ids"].to(device)
            labels = batch["label"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )

            total_loss += outputs.loss.item()

            predictions = outputs.logits.argmax(dim=-1)
            total_correct += (predictions == labels).sum().item()
            total_samples += labels.size(0)

            # Binary metrics for BUG (label == 1)
            true_positives += ((predictions == 1) & (labels == 1)).sum().item()
            false_positives += ((predictions == 1) & (labels == 0)).sum().item()
            false_negatives += ((predictions == 0) & (labels == 1)).sum().item()

    avg_loss = total_loss / len(dataloader) if len(dataloader) > 0 else 0.0
    accuracy = (total_correct / total_samples * 100) if total_samples > 0 else 0.0

    precision = (
        (true_positives / (true_positives + false_positives) * 100)
        if (true_positives + false_positives) > 0
        else 0.0
    )
    recall = (
        (true_positives / (true_positives + false_negatives) * 100)
        if (true_positives + false_negatives) > 0
        else 0.0
    )
    f1 = (
        (2 * precision * recall / (precision + recall))
        if (precision + recall) > 0
        else 0.0
    )

    return avg_loss, accuracy, precision, recall, f1


def predict_snippet(model, tokenizer, code_text, device):
    """
    Runs bug-detection inference on a single code snippet.
    Returns predicted label ('CLEAN' or 'BUG') and confidence score.
    """
    model.eval()
    inputs = tokenizer(
        code_text,
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]
        pred_id = torch.argmax(probs).item()
        confidence = probs[pred_id].item() * 100

    label_str = "BUG" if pred_id == 1 else "CLEAN"
    return label_str, confidence


def main():
    # ==========================================
    # 1. HARDWARE SETUP
    # ==========================================
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}\n")

    # ==========================================
    # 2. LOAD FINE-TUNED MODEL & TOKENIZER
    # ==========================================
    model_dir = "masteries/coding/models/critic_v1"
    print(f"Loading fine-tuned critic model from: {model_dir}")

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(device)
    print(
        f"Model loaded  –  {sum(p.numel() for p in model.parameters()):,} parameters\n"
    )

    # ==========================================
    # 3. PREPARE TEST SPLIT
    # ==========================================
    paths = [
        "masteries/coding/data/raw/critic_raw_constants.parquet",
        "masteries/coding/data/raw/critic_raw_deletions.parquet",
        "masteries/coding/data/raw/critic_raw_flips.parquet",
    ]
    full_dataset = CoderCriticDataset(
        parquet_paths=paths,
        tokenizer=tokenizer,
        max_length=512,
    )

    # Use 5% of the data as a test set (fast but representative)
    test_size = max(1, int(len(full_dataset) * 0.05))
    _, test_dataset = random_split(
        full_dataset,
        [len(full_dataset) - test_size, test_size],
        generator=torch.Generator().manual_seed(42),
    )

    test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False)
    print(f"Test split: {len(test_dataset)} samples  ({len(test_loader)} batches)\n")

    # ==========================================
    # 4. EVALUATION – Loss / Accuracy / F1
    # ==========================================
    print("=" * 60)
    print("  EVALUATION RESULTS")
    print("=" * 60)

    avg_loss, accuracy, precision, recall, f1 = evaluate(model, test_loader, device)

    print(f"\n  Average Loss : {avg_loss:.4f}")
    print(f"  Accuracy     : {accuracy:.2f}%")
    print(f"  Precision    : {precision:.2f}%")
    print(f"  Recall       : {recall:.2f}%")
    print(f"  F1 Score     : {f1:.2f}%\n")

    # ==========================================
    # 5. BUG DETECTION DEMO – Sample Snippets
    # ==========================================
    print("=" * 60)
    print("  BUG DETECTION DEMO")
    print("=" * 60)

    sample_snippets = [
        {
            "name": "Clean Binary Search",
            "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
        },
        {
            "name": "Buggy Binary Search (Flipped Operator / Constant Mutation)",
            "code": "def binary_search(arr, target):\n    left, right = 0, len(arr) + 1\n    while left > right:\n        mid = (left - right) // 2\n        if arr[mid] != target:\n            return mid\n        elif arr[mid] < target:\n            left = mid - 1\n        else:\n            right = mid + 1\n    return -1",
        },
    ]

    for sample in sample_snippets:
        print(f"\nSnippet: {sample['name']}")
        print("-" * 60)
        print(sample["code"])
        print("-" * 60)
        pred_label, conf = predict_snippet(model, tokenizer, sample["code"], device)
        print(f"Prediction: {pred_label} (Confidence: {conf:.2f}%)\n")

    print("Test complete.")


if __name__ == "__main__":
    main()
