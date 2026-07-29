import torch
import gc
import sys
import os

# Add parent dir to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from masteries.coding.utils.thermal_guard import assert_safe_thermals

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
)

# ==========================================
# HARDWARE SETTINGS
# ==========================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
N_CANDIDATES = 3
BUG_THRESHOLD = 0.50

ACTOR_PATH = "masteries/coding/models/actor_v1"
CRITIC_PATH = "masteries/coding/models/critic_best"


def flush_vram():
    """Forces PyTorch to release memory back to the OS."""
    gc.collect()
    torch.cuda.empty_cache()


def load_actor():
    print("\n[VRAM] Loading Actor...")
    assert_safe_thermals()
    tokenizer = AutoTokenizer.from_pretrained(ACTOR_PATH)
    model = AutoModelForCausalLM.from_pretrained(ACTOR_PATH).to(device)
    return tokenizer, model


def load_critic():
    print("\n[VRAM] Loading Critic...")
    assert_safe_thermals()
    tokenizer = AutoTokenizer.from_pretrained(CRITIC_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(CRITIC_PATH).to(device)
    return tokenizer, model


def v2_pipeline_best_of_n(user_prompt):
    print("--- INITIATING BEST-OF-N (N=3) PIPELINE ---")

    candidates = []

    # ----------------------------------------
    # PHASE 1: ACTOR GENERATION (N Candidates)
    # ----------------------------------------
    actor_tok, actor_mod = load_actor()
    inputs = actor_tok(user_prompt, return_tensors="pt").to(device)

    print("\n[PHASE 1] Generating Candidates...")
    for i in range(1, N_CANDIDATES + 1):
        outputs = actor_mod.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.65,
            top_p=0.90,
            do_sample=True,
            pad_token_id=actor_tok.eos_token_id,
            eos_token_id=actor_tok.eos_token_id,
        )
        generated_code = actor_tok.decode(outputs[0], skip_special_tokens=True)
        generated_code = generated_code.replace(user_prompt, "").strip()
        candidates.append(generated_code)
        print(f"Candidate {i} generated.")

    del actor_tok, actor_mod
    flush_vram()

    # ----------------------------------------
    # PHASE 2: CRITIC SCORING
    # ----------------------------------------
    critic_tok, critic_mod = load_critic()

    best_code = None
    best_score = 1.0

    print("\n[PHASE 2] Critic Scoring...")
    for i, code in enumerate(candidates):
        c_inputs = critic_tok(
            code, return_tensors="pt", truncation=True, max_length=512
        ).to(device)

        with torch.no_grad():
            logits = critic_mod(**c_inputs).logits
            probs = torch.softmax(logits, dim=1)
            bug_prob = probs[0][1].item()

        print(f"Candidate {i+1} Score: {bug_prob:.4f} Bug Probability")

        if bug_prob < best_score:
            best_score = bug_prob
            best_code = code

    del critic_tok, critic_mod
    flush_vram()

    # ----------------------------------------
    # PHASE 3: SELECTION
    # ----------------------------------------
    if best_score > BUG_THRESHOLD:
        print("\n⚠️ [WARNING: High Risk Code]")
        print(
            f"All {N_CANDIDATES} candidates exceeded bug threshold. Returning safest option (Score: {best_score:.4f})."
        )
        return f"# [WARNING: High Risk Code - Bug Prob: {best_score:.4f}]\n{best_code}"
    else:
        print(f"\n✅ [SUCCESS] Returning best candidate (Score: {best_score:.4f}).")
        return best_code


if __name__ == "__main__":
    test_prompt = "def fibonacci(n):"
    final_output = v2_pipeline_best_of_n(test_prompt)

    print("\n\n🏆 FINAL SYSTEM OUTPUT 🏆")
    print("-----------------------------------")
    print(final_output)
    print("-----------------------------------")
