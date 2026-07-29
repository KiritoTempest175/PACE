import os
import pandas as pd
import datasets


def main():
    OUTPUT_DIR = "masteries/coding/data/raw"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    OUTPUT_PATH = os.path.join(OUTPUT_DIR, "codeforces_fused_dataset.parquet")

    print("Loading open-r1/codeforces-submissions dataset (streaming mode)...")
    ds = datasets.load_dataset(
        "open-r1/codeforces-submissions", split="train", streaming=True
    )

    clean_data = []
    buggy_data = []

    # Target dataset size: 50k clean, 50k buggy
    TARGET_PER_CLASS = 50000

    print(f"Extracting up to {TARGET_PER_CLASS} Python samples per class...")

    for item in ds:
        lang = str(item.get("programmingLanguage", "")).lower()
        if "python" not in lang and "pypy" not in lang:
            continue

        verdict = item.get("verdict", "")
        code = item.get("source", "")

        if verdict == "OK" and len(clean_data) < TARGET_PER_CLASS:
            clean_data.append({"mutated_code": code, "label": "CLEAN"})
        elif (
            verdict in ["WRONG_ANSWER", "TIME_LIMIT_EXCEEDED", "RUNTIME_ERROR"]
            and len(buggy_data) < TARGET_PER_CLASS
        ):
            buggy_data.append({"mutated_code": code, "label": "BUG"})

        # Stop early if we have enough data
        if len(clean_data) >= TARGET_PER_CLASS and len(buggy_data) >= TARGET_PER_CLASS:
            break

    print(f"Extracted {len(clean_data)} CLEAN samples.")
    print(f"Extracted {len(buggy_data)} BUGGY samples.")

    df_clean = pd.DataFrame(clean_data)
    df_bugs = pd.DataFrame(buggy_data)

    print("Fusing and randomizing dataset...")
    df_fused = pd.concat([df_clean, df_bugs], ignore_index=True)

    # Remove completely duplicated snippets
    df_fused = df_fused.drop_duplicates(
        subset=["mutated_code"], keep="first"
    ).reset_index(drop=True)

    # Final deep shuffle
    df_fused = df_fused.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"Saving to {OUTPUT_PATH}...")
    df_fused.to_parquet(OUTPUT_PATH)

    print(f"SUCCESS! Dataset saved to {OUTPUT_PATH}")
    print(f"Total Rows: {len(df_fused)}")
    print(
        f"Clean Data: {(df_fused['label'] == 'CLEAN').sum()} | Bug Data: {(df_fused['label'] == 'BUG').sum()}"
    )


if __name__ == "__main__":
    main()
