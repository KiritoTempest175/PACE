import pandas as pd
from torch.utils.data import Dataset


class CoderCriticDataset(Dataset):
    def __init__(self, parquet_path):

        self.df = pd.read_parquet(parquet_path)

    def __len__(self):

        return len(self.df)

    def __getitem__(self, idx):

        row = self.df.iloc[idx]

        return {"code": row["mutated_code"], "label": row["label"]}


# --- Quick Test Block ---
"""
if __name__ == "__main__":

    test_path = "masteries/coding/data/raw/critic_raw_flips.parquet"

    print("Testing CoderCriticDataset...")
    dataset = CoderCriticDataset(test_path)

    print(f"Total rows in dataset: {len(dataset)}")
    print("\nFetching Row 0:")
    print(dataset[0])
"""
