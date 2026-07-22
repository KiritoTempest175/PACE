"""
PACE (Pipelined Actor-Critic Ensemble) - Phase 2
Critic Model Training Pipeline & Hardware State Machine

Enforces strict NVIDIA RTX 4060 VRAM memory management and multi-epoch
sequence classification training using DistilGPT-2.
"""

import gc
import os
import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from masteries.coding.training.critic.dataset import CoderCriticDataset


def get_critic_dataloader(parquet_path, batch_size=8, shuffle=True):

    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
    tokenizer.pad_token = tokenizer.eos_token

    dataset = CoderCriticDataset(
        parquet_path=parquet_path,
        tokenizer=tokenizer,
        max_length=512,
    )

    loader = DataLoader(
        dataset=dataset,
        batch_size=8,
        shuffle=True,
        num_workers=0,
        pin_memory=torch.cuda.is_available(),
    )

    return loader, tokenizer


def test_data_pipeline():

    print("[SYSTEM] Initializing Data Delivery Pipeline...")

    train_loader, _ = get_critic_dataloader(
        "masteries/coding/data/raw/critic_raw_deletions.parquet"
    )
    print(f"[SUCCESS] DataLoader configured with {len(train_loader)} total batches.")

    print("[SYSTEM] Fetching test batch from pipeline...")
    test_batch = next(iter(train_loader))

    print("\n--- BATCH MATRIX VERIFICATION ---")
    print(
        f"Input IDs Shape:      {test_batch['input_ids'].shape}      | Expected: [batch_size, 512]"
    )
    print(
        f"Attention Mask Shape: {test_batch['attention_mask'].shape} | Expected: [batch_size, 512]"
    )
    print(
        f"Labels Shape:         {test_batch['label'].shape}          | Expected: [batch_size]"
    )
    print(
        f"Input IDs Data Type:  {test_batch['input_ids'].dtype}     | Expected: torch.int64"
    )
    print(
        f"Labels Data Type:     {test_batch['label'].dtype}        | Expected: torch.int64"
    )
    print("---------------------------------\n")


def test_vram_state_machine():
    print("\n[SYSTEM] Initializing Model & VRAM State Machine Test...")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[HARDWARE] Active Compute Device: {device.type.upper()}")

    if device.type == "cuda":
        print(f"[HARDWARE] GPU Name: {torch.cuda.get_device_name(0)}")
        print(
            f"[VRAM] Initial Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
        )

    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
    tokenizer.pad_token = tokenizer.eos_token

    print("[SYSTEM] Loading DistilGPT-2 with Sequence Classification Head...")
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilgpt2", num_labels=2
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model = model.to(device)

    if device.type == "cuda":
        print(
            f"[VRAM] Post-Model Load Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
        )

    print("[SYSTEM] Executing VRAM State Machine Teardown Sequence...")
    del model
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
        print(
            f"[VRAM] Post-Purge Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB (Target: ~0.00 MB)"
        )

    print("[SUCCESS] VRAM State Machine cycle completed cleanly.")


def train_critic(
    epochs=2, batch_size=8, lr=5e-5, output_dir="masteries/coding/artifacts/critic_v1"
):

    print(f"\n[SYSTEM] Initializing PACE Critic Training Pipeline ({epochs} Epochs)...")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[HARDWARE] Training execution locked to: {device.type.upper()}")

    train_loader, tokenizer = get_critic_dataloader(
        parquet_path="masteries/coding/data/raw/critic_raw_deletions.parquet",
        batch_size=batch_size,
        shuffle=True,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        "distilgpt2", num_labels=2
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model = model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    for epoch in range(epochs):
        print(f"\n---> STARTING EPOCH {epoch + 1}/{epochs} <---")
        model.train()

        total_train_loss = 0.0

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            optimizer.zero_grad()
            outputs = model(
                input_ids=input_ids, attention_mask=attention_mask, labels=labels
            )
            loss = outputs.loss

            loss.backward()
            optimizer.step()

            total_train_loss += loss.item()

            if step % 25 == 0:
                print(
                    f"[EPOCH {epoch + 1} | STEP {step:03d}/{len(train_loader)}] Current Batch Loss: {loss.item():.4f}"
                )

        avg_epoch_loss = total_train_loss / len(train_loader)
        print(f"---> EPOCH {epoch + 1} COMPLETE | Average Loss: {avg_epoch_loss:.4f}")

    print(f"\n[SYSTEM] Serializing trained Critic micro-model to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print("[SUCCESS] Checkpoint saved! Micro-model ready for Actor-Critic loop.")

    del model, optimizer, train_loader
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
        print(
            f"[VRAM] Pipeline Purged. Idling Context Footprint: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
        )


# =====================================================================
# PRODUCTION ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    # --- Regression Test Suite (Uncomment to diagnose hardware/pipeline issues) ---
    # test_data_pipeline()
    # test_vram_state_machine()

    # --- Production Training Execution ---
    train_critic(
        epochs=2,
        batch_size=8,
        lr=5e-5,
        output_dir="masteries/coding/artifacts/critic_v1",
    )
