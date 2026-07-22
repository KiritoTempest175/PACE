from torch.utils.data import DataLoader
from transformers import AutoTokenizer
from masteries.coding.training.critic.dataset import CoderCriticDataset


def test_data_pipeline():
    print("[SYSTEM] Initializing Data Delivery Pipeline...")

    print("[SYSTEM] Loading DistilGPT-2 Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")

    tokenizer.pad_token = tokenizer.eos_token

    train_dataset = CoderCriticDataset(
        parquet_path="masteries/coding/data/raw/critic_raw_deletions.parquet",
        tokenizer=tokenizer,
        max_length=512,
    )

    train_loader = DataLoader(
        dataset=train_dataset,
        batch_size=8,
        shuffle=True,
        num_workers=0,
        pin_memory=True,
    )

    print(f"[SUCCESS] DataLoader configured with {len(train_loader)} total batches.")

    print("[SYSTEM] Fetching test batch from pipeline...")
    batch_iterator = iter(train_loader)
    test_batch = next(batch_iterator)

    input_ids = test_batch["input_ids"]
    attention_mask = test_batch["attention_mask"]
    labels = test_batch["label"]

    print("\n--- BATCH MATRIX VERIFICATION ---")
    print(f"Input IDs Shape:      {input_ids.shape}      | Expected: [batch_size, 512]")
    print(f"Attention Mask Shape: {attention_mask.shape} | Expected: [batch_size, 512]")
    print(f"Labels Shape:         {labels.shape}          | Expected: [batch_size]")
    print(f"Input IDs Data Type:  {input_ids.dtype}     | Expected: torch.int64")
    print(f"Labels Data Type:     {labels.dtype}        | Expected: torch.int64")
    print("---------------------------------\n")


if __name__ == "__main__":
    test_data_pipeline()
