"""
PACE Critic Full Training Loop
Task: Train a 125M parameter CodeBERT classifier to detect bugs (0 = Clean, 1 = Bug).
"""

import os
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
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

    paths = ["masteries/coding/data/raw/critic_fused_dataset.parquet"]

    dataset = CoderCriticDataset(
        parquet_paths=paths,
        tokenizer=tokenizer,
        max_length=512,
    )
    loader = DataLoader(dataset, batch_size=8, shuffle=True)
    # ==========================================
    # 3. NEURAL NETWORK SETUP
    # ==========================================
    print("Loading 125M Parameter Critic Model to GPU...")

    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, num_labels=2
    ).to(device)
    optimizer = AdamW(model.parameters(), lr=5e-5)

    # ==========================================
    # 4. THE FULL TRAINING LOOP
    # ==========================================
    epochs = 1
    save_dir = "masteries/coding/models/critic_v1"

    print(f"Starting Critic Training Loop for {epochs} Epoch(s)...")

    for epoch in range(epochs):

        model.train()
        progress_bar = tqdm(loader, desc="Training")
        total_loss = 0

        for batch in progress_bar:

            input_ids = batch["input_ids"].to(device)
            labels = batch["label"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            outputs = model(
                input_ids=input_ids, attention_mask=attention_mask, labels=labels
            )
            loss = outputs.loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            current_loss = loss.item()
            total_loss += current_loss
            progress_bar.set_postfix({"loss": f"{current_loss:.4f}"})

        avg_loss = total_loss / len(loader)
        print(f"\nEpoch {epoch + 1} completed. Average Loss: {avg_loss:.4f}")

        # ==========================================
        # 5. SAVE THE MODEL WEIGHTS
        # ==========================================

        print(f"Saving model checkpoint to {save_dir}...")
        os.makedirs(save_dir, exist_ok=True)

        model.save_pretrained(save_dir)
        tokenizer.save_pretrained(save_dir)

        print("Model saved successfully!")


if __name__ == "__main__":
    main()
