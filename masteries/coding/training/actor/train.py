"""
PACE Actor Full Training Loop
"""

import os
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM
from torch.optim import AdamW
from tqdm import tqdm

from dataset import CoderActorDataset


def main():
    # ==========================================
    # 1. HARDWARE SETUP
    # ==========================================
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # ==========================================
    # 2. DATA PIPELINE
    # ==========================================
    model_name = "bigcode/tiny_starcoder_py"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    dataset = CoderActorDataset(
        parquet_path="masteries/coding/data/raw/stack_python_157k.parquet",
        tokenizer=tokenizer,
        max_length=512,
    )
    loader = DataLoader(dataset, batch_size=4, shuffle=True)

    # ==========================================
    # 3. NEURAL NETWORK SETUP
    # ==========================================
    print("Loading 164M Parameter Actor Model to GPU...")

    model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

    optimizer = AdamW(model.parameters(), lr=5e-5)

    # ==========================================
    # 4. THE FULL TRAINING LOOP
    # ==========================================
    epochs = 1
    save_dir = "masteries/coding/models/actor_v1"

    print(f"Starting Full Training Loop for {epochs} Epoch(s)...")
    model.train()

    for epoch in range(epochs):
        print(f"\n--- Epoch {epoch + 1}/{epochs} ---")

        progress_bar = tqdm(loader, desc="Training")

        total_loss = 0

        for batch in progress_bar:
            input_ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)
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
