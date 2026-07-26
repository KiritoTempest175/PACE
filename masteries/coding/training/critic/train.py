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
    # Set up your device to use CUDA if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ==========================================
    # 2. DATA PIPELINE
    # ==========================================
    model_name = "microsoft/codebert-base"

    # Initialize the AutoTokenizer using model_name
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    # Define your paths list containing all 3 mutated parquet files
    paths = [
        "masteries/coding/data/raw/critic_raw_constants.parquet",
        "masteries/coding/data/raw/critic_raw_deletions.parquet",
        "masteries/coding/data/raw/critic_raw_flips.parquet",
    ]

    # Initialize CoderCriticDataset (pass paths, tokenizer, and max_length=512)
    # Initialize DataLoader (batch_size=8, shuffle=True)
    dataset = CoderCriticDataset(
        parquet_paths=paths,
        tokenizer=tokenizer,
        max_length=512,
    )
    loader = DataLoader(dataset, batch_size=4, shuffle=True)
    # ==========================================
    # 3. NEURAL NETWORK SETUP
    # ==========================================
    print("Loading 125M Parameter Critic Model to GPU...")

    # Initialize AutoModelForSequenceClassification
    # CRITICAL: You MUST pass the argument `num_labels=2` so it knows there are only 2 possible outputs (0 or 1)
    # Chain .to(device) to push it to the GPU
    # Initialize the AdamW optimizer (lr=5e-5)

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
    # Set model to train mode

    for epoch in range(epochs):
        # Create your tqdm progress bar over the loader
        # Initialize total_loss = 0
        model.train()
        progress_bar = tqdm(loader, desc="Training")
        total_loss = 0

        for batch in progress_bar:
            # Move input_ids, labels, and attention_mask to device
            input_ids = batch["input_ids"].to(device)
            labels = batch["label"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            # Forward pass (outputs = model(...))
            # Extract loss
            outputs = model(
                input_ids=input_ids, attention_mask=attention_mask, labels=labels
            )
            loss = outputs.loss

            # The Holy Trinity (zero_grad, backward, step)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Update progress bar postfix with current loss
            current_loss = loss.item()
            total_loss += current_loss
            progress_bar.set_postfix({"loss": f"{current_loss:.4f}"})

        # Calculate and print epoch average loss
        avg_loss = total_loss / len(loader)
        print(f"\nEpoch {epoch + 1} completed. Average Loss: {avg_loss:.4f}")

        # ==========================================
        # 5. SAVE THE MODEL WEIGHTS
        # ==========================================
        # Create the save_dir using os.makedirs
        # Save the model and the tokenizer
        print(f"Saving model checkpoint to {save_dir}...")
        os.makedirs(save_dir, exist_ok=True)

        model.save_pretrained(save_dir)
        tokenizer.save_pretrained(save_dir)

        print("Model saved successfully!")


if __name__ == "__main__":
    main()
