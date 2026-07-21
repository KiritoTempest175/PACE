import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer


class CoderCriticDataset(Dataset):
    def __init__(self, parquet_path, tokenizer, max_length=512):
        """
        Loads the parquet dataset from disk and attaches the tokenizer.
        """
        self.df = pd.read_parquet(parquet_path)
        self.tokenizer = tokenizer
        self.max_length = max_length

        # Map text labels to mathematical integers for the GPU
        self.label_map = {"CLEAN": 0, "BUG": 1}

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        code_text = row["mutated_code"]
        raw_label = row["label"]

        # 1. Tokenize the code (Truncate long code, Pad short code to max_length)
        encoding = self.tokenizer(
            code_text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )

        # 2. Translate label string ("BUG" / "CLEAN") to an integer (1 / 0)
        label_int = self.label_map.get(raw_label, 1)

        # We use .squeeze(0) to turn shape [1, max_len] into a clean 1D array [max_len]
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label_int, dtype=torch.long),
        }


# --- Quick Test Block ---
if __name__ == "__main__":
    print("Loading Tokenizer and Testing Updated CoderCriticDataset...")
    test_tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
    test_tokenizer.pad_token = test_tokenizer.eos_token

    # Pointing to your raw data
    test_path = "masteries/coding/data/raw/critic_raw_flips.parquet"
    dataset = CoderCriticDataset(test_path, test_tokenizer, max_length=32)

    print(f"Total rows: {len(dataset)}")
    print("\nFetching Row 0 (Translated to GPU Math):")
    sample = dataset[0]
    print("Input IDs shape:", sample["input_ids"].shape)
    print("Input IDs:", sample["input_ids"])
    print("Attention Mask:", sample["attention_mask"])
    print("Label:", sample["label"])
