import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_dir = "masteries/coding/models/critic_best"

print("Loading Critic...")
tokenizer = AutoTokenizer.from_pretrained(model_dir)
model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(device)
model.eval()

clean_code = """
def multiply(a, b):
    return a * b
"""

buggy_code = """
def multiply(a, b):
    return a + b
"""


def predict_bug(code_str):
    inputs = tokenizer(
        code_str, return_tensors="pt", truncation=True, max_length=512
    ).to(device)
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=1)
        # Class 1 is "BUG"
        return probs[0][1].item()


print(f"\n[CLEAN CODE] Bug Probability: {predict_bug(clean_code):.4f}")
print(f"[BUGGY CODE] Bug Probability: {predict_bug(buggy_code):.4f}")
