"""
PACE Critic Full Training Loop
Task: Train a 125M parameter CodeBERT classifier to detect bugs (0 = Clean, 1 = Bug).
"""

import os
import torch
from torch.utils.data import DataLoader, random_split
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    get_cosine_schedule_with_warmup,
)
from torch.optim import AdamW
from tqdm import tqdm

from dataset import CoderCriticDataset


def main():
    # ==========================================
    # 1. HARDWARE SETUP
    # ==========================================

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ==========================================
    # 2. DATA PIPELINE
    # ==========================================
    model_name = "microsoft/codebert-base"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    paths = ["masteries/coding/data/raw/codecontests_fused_dataset.parquet"]

    full_dataset = CoderCriticDataset(
        parquet_paths=paths,
        tokenizer=tokenizer,
        max_length=512,
    )

    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)

    # ==========================================
    # 3. NEURAL NETWORK SETUP
    # ==========================================
    print("Loading 125M Parameter Critic Model to GPU...")

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=2
    ).to(device)

    # Differential learning rates: smaller for pre-trained backbone, larger for random head
    optimizer = AdamW(
        [
            {"params": model.roberta.parameters(), "lr": 2e-5},
            {"params": model.classifier.parameters(), "lr": 1e-3},
        ],
        weight_decay=0.01,
    )

    # ==========================================
    # 4. THE FULL TRAINING LOOP
    # ==========================================
    epochs = 10
    accumulation_steps = 4
    save_dir = "masteries/coding/models/critic_v3"

    num_training_steps = epochs * (len(train_loader) // accumulation_steps)
    lr_scheduler = get_cosine_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=int(0.1 * num_training_steps),
        num_training_steps=num_training_steps,
    )

    print(f"Starting Critic Training Loop for {epochs} Epoch(s)...")

    best_val_acc = 0.0

    for epoch in range(epochs):

        model.train()
        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{epochs} [Train]")
        total_loss = 0
        optimizer.zero_grad()

        for batch_idx, batch in enumerate(progress_bar):

            input_ids = batch["input_ids"].to(device)
            labels = batch["label"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            outputs = model(
                input_ids=input_ids, attention_mask=attention_mask, labels=labels
            )
            loss = outputs.loss / accumulation_steps
            loss.backward()

            if (batch_idx + 1) % accumulation_steps == 0 or (batch_idx + 1) == len(
                train_loader
            ):
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                lr_scheduler.step()
                optimizer.zero_grad()

            current_loss = loss.item() * accumulation_steps
            total_loss += current_loss
            progress_bar.set_postfix({"loss": f"{current_loss:.4f}"})

        avg_loss = total_loss / len(train_loader)

        # Validation Phase
        model.eval()
        val_loss = 0
        correct_preds = 0
        total_preds = 0

        val_progress = tqdm(val_loader, desc=f"Epoch {epoch + 1}/{epochs} [Val]")
        with torch.no_grad():
            for batch in val_progress:
                input_ids = batch["input_ids"].to(device)
                labels = batch["label"].to(device)
                attention_mask = batch["attention_mask"].to(device)

                outputs = model(
                    input_ids=input_ids, attention_mask=attention_mask, labels=labels
                )
                val_loss += outputs.loss.item()

                preds = torch.argmax(outputs.logits, dim=1)
                correct_preds += (preds == labels).sum().item()
                total_preds += labels.size(0)

        avg_val_loss = val_loss / len(val_loader)
        val_acc = correct_preds / total_preds

        print(
            f"\nEpoch {epoch + 1} completed. Train Loss: {avg_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.4f}"
        )

        # ==========================================
        # 5. SAVE THE MODEL WEIGHTS
        # ==========================================
        if val_acc > best_val_acc:
            print(
                f"Validation accuracy improved from {best_val_acc:.4f} to {val_acc:.4f}. Saving model to {save_dir}..."
            )
            best_val_acc = val_acc
            os.makedirs(save_dir, exist_ok=True)
            model.save_pretrained(save_dir)
            tokenizer.save_pretrained(save_dir)
            print("Model saved successfully!")
        else:
            print(
                f"Validation accuracy did not improve from {best_val_acc:.4f}. Not saving."
            )


if __name__ == "__main__":
    main()
