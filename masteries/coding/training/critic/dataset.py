import torch
from torch.utils.data import Dataset
import pandas as pd


class CoderCriticDataset(Dataset):
    def __init__(self, parquet_paths, tokenizer, max_length=512):
        self.tokenizer = tokenizer
        self.max_length = max_length

        # Load and fuse the dataframes
        dfs = [pd.read_parquet(p) for p in parquet_paths]
        self.df = pd.concat(dfs, ignore_index=True)

        # ==========================================
        # CRITICAL FIX: MAP STRINGS TO INTEGERS
        # CLEAN = 0, BUG = 1
        # ==========================================
        label_mapping = {"CLEAN": 0, "BUG": 1}
        self.df["label"] = self.df["label"].map(label_mapping)

        # Drop any rows where mapping failed (just in case)
        self.df = self.df.dropna(subset=["label"])

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        code_snippet = str(row["mutated_code"])

        # Tokenize the snippet
        encoding = self.tokenizer(
            code_snippet,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )

        # Return the cleanly formatted dictionary for train.py
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(row["label"], dtype=torch.long),  # Must be torch.long
        }


if __name__ == "__main__":
    from transformers import AutoTokenizer

    print("Loading Tokenizer and Testing Updated CoderCriticDataset...")
    test_tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

    paths = ["masteries/coding/data/raw/critic_fused_dataset.parquet"]

    dataset = CoderCriticDataset(paths, test_tokenizer, max_length=32)

    print("\nFetching Row 0 (Translated to GPU Math):")
    sample = dataset[0]
    print("Input IDs shape:", sample["input_ids"].shape)
    print("Label:", sample["label"])
