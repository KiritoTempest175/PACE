"""
PACE Actor Dataset
Task: Ingests clean Python code, tokenizes it, and duplicates the input_ids to act as causal LM labels.
"""

import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer


class CoderActorDataset(Dataset):
    def __init__(self, parquet_path, tokenizer, max_length=512):
        # ==========================================
        # 1. INITIALIZATION
        # ==========================================
        self.df = pd.read_parquet(parquet_path)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        # ==========================================
        # 2. DATA EXTRACTION
        # ==========================================
        clean_code_text = self.df.iloc[idx]["content"]

        # ==========================================
        # 3. TOKENIZATION
        # ==========================================
        inputs = self.tokenizer(
            clean_code_text,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",  # FIXED: Passed as a string command
            return_tensors="pt",
        )

        input_ids = inputs["input_ids"].squeeze(0)
        attention_mask = inputs["attention_mask"].squeeze(0)

        # ==========================================
        # 4. FORMATTING CAUSAL LABELS
        # ==========================================
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": input_ids.clone(),  # Cloned safely for causal LM
        }


# =====================================================================
# SYSTEM TEST ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    tokenizer = AutoTokenizer.from_pretrained("bigcode/tiny_starcoder_py")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    test_path = "masteries/coding/data/raw/stack_python_157k.parquet"
    dataset = CoderActorDataset(test_path, tokenizer, max_length=32)
    print(f"Total rows: {len(dataset)}")

    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
    for batch in dataloader:
        print("Input IDs Shape:", batch["input_ids"].shape)
        print("Labels Shape:", batch["labels"].shape)
        break
