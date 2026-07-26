import pandas as pd
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer


class CoderCriticDataset(Dataset):
    def __init__(self, parquet_paths, tokenizer, max_length=512):

        print("Fusing datasets...")
        dfs = [pd.read_parquet(path) for path in parquet_paths]

        self.df = pd.concat(dfs, ignore_index=True)

        self.df = self.df.sample(frac=1, random_state=42).reset_index(drop=True)

        self.tokenizer = tokenizer
        self.max_length = max_length

        self.label_map = {"CLEAN": 0, "BUG": 1}
        print(f"Dataset fused & shuffled. Total Critic rows: {len(self.df)}")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        code_text = row["mutated_code"]
        raw_label = row["label"]

        encoding = self.tokenizer(
            code_text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )

        label_int = self.label_map.get(raw_label, 1)

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label_int, dtype=torch.long),
        }


if __name__ == "__main__":
    print("Loading Tokenizer and Testing Updated CoderCriticDataset...")
    test_tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

    paths = [
        "masteries/coding/data/raw/critic_raw_constants.parquet",
        "masteries/coding/data/raw/critic_raw_deletions.parquet",
        "masteries/coding/data/raw/critic_raw_flips.parquet",
    ]

    dataset = CoderCriticDataset(paths, test_tokenizer, max_length=32)

    print("\nFetching Row 0 (Translated to GPU Math):")
    sample = dataset[0]
    print("Input IDs shape:", sample["input_ids"].shape)
    print("Label:", sample["label"])
