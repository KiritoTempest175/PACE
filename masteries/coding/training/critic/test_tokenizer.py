from transformers import AutoTokenizer

print("Loading the Tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("distilgpt2")

tokenizer.pad_token = tokenizer.eos_token

sample_code_1 = "def add(a, b):\n    return a + b"
sample_code_2 = "def short(): pass"
batch = [sample_code_1, sample_code_2]


tokens = tokenizer(
    batch,
    padding="max_length",  # Pad short sequences to reach max_length
    truncation=True,  # Chop off long sequences if they exceed max_length
    max_length=15,  # Force every row to be exactly 15 tokens long
    return_tensors="pt",  # Return PyTorch Tensors ("pt") instead of standard Python lists
)

print("\n--- 1. INPUT IDs (The Perfect Rectangular Matrix) ---")
print(tokens["input_ids"])

print("\n--- 2. ATTENTION MASK (1 = Read this, 0 = Ignore this padding) ---")
print(tokens["attention_mask"])
