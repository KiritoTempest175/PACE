import torch
import gc
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
)

# ==========================================
# HARDWARE SETTINGS
# ==========================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_RETRIES = 3
BUG_THRESHOLD = 0.50  # If probability > 50%, it's rejected.

# Model Paths (Update Actor path as needed)
ACTOR_PATH = "masteries/coding/models/actor_v1"  # Assuming you have a local actor path
CRITIC_PATH = "masteries/coding/models/critic_v3"


def flush_vram():
    """Forces PyTorch to release memory back to the OS."""
    torch.cuda.empty_cache()
    gc.collect()


def load_actor():
    print("\n[VRAM] Loading Actor...")
    tokenizer = AutoTokenizer.from_pretrained(ACTOR_PATH)
    model = AutoModelForCausalLM.from_pretrained(ACTOR_PATH).to(device)
    return tokenizer, model


def load_critic():
    print("\n[VRAM] Loading Critic...")
    tokenizer = AutoTokenizer.from_pretrained(CRITIC_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(CRITIC_PATH).to(device)
    return tokenizer, model


def v2_pipeline(user_prompt):
    print("--- INITIATING V2 ACTIVE PIPELINE ---")

    current_prompt = user_prompt
    best_code = None
    best_score = 1.0  # Start with max bug probability

    for attempt in range(1, MAX_RETRIES + 1):
        print("\n==========================================")
        print(f" 🔄 ATTEMPT {attempt} / {MAX_RETRIES}")
        print("==========================================")

        # ----------------------------------------
        # PHASE 1: ACTOR GENERATION
        # ----------------------------------------
        actor_tok, actor_mod = load_actor()

        inputs = actor_tok(current_prompt, return_tensors="pt").to(device)

        outputs = actor_mod.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.2,  # Low temperature keeps generation deterministic & focused on code
            top_p=0.95,
            do_sample=True,
            pad_token_id=actor_tok.eos_token_id,
            eos_token_id=actor_tok.eos_token_id,
        )

        generated_code = actor_tok.decode(outputs[0], skip_special_tokens=True)

        # Strip out the prompt so we only evaluate the new code
        generated_code = generated_code.replace(current_prompt, "").strip()
        print(f"\n[ACTOR GENERATED]:\n{generated_code}")

        del actor_tok, actor_mod
        flush_vram()

        # ----------------------------------------
        # PHASE 2: CRITIC VALIDATION
        # ----------------------------------------
        critic_tok, critic_mod = load_critic()

        c_inputs = critic_tok(
            generated_code, return_tensors="pt", truncation=True, max_length=512
        ).to(device)
        with torch.no_grad():
            logits = critic_mod(**c_inputs).logits
            probs = torch.softmax(logits, dim=1)
            bug_probability = probs[0][1].item()  # Probability of Class 1 (BUG)

        print(f"\n[CRITIC SCORE]: {bug_probability:.4f} Bug Probability")

        # Save the safest code just in case we fail all attempts
        if bug_probability < best_score:
            best_score = bug_probability
            best_code = generated_code

        del critic_tok, critic_mod
        flush_vram()

        # ----------------------------------------
        # PHASE 3: THE SELF-CORRECTION DECISION
        # ----------------------------------------
        if bug_probability < BUG_THRESHOLD:
            print(f"\n✅ [SUCCESS] Code passed validation on attempt {attempt}!")
            return generated_code
        else:
            print("❌ [FAILED] Critic caught a bug. Routing back to Actor...")
            # Update the prompt to tell the Actor to fix its mistake
            current_prompt = (
                f"{user_prompt}\n\n"
                f"# The following code you generated failed syntax/logic validation:\n"
                f"{generated_code}\n\n"
                f"# Please rewrite and fix the errors:"
            )

    print(f"\n⚠️ [WARNING] Failed to generate clean code after {MAX_RETRIES} attempts.")
    print(f"Returning safest candidate (Score: {best_score:.4f})")
    return best_code


if __name__ == "__main__":
    test_prompt = "def fibonacci(n):"
    final_output = v2_pipeline(test_prompt)

    print("\n\n🏆 FINAL SYSTEM OUTPUT 🏆")
    print("-----------------------------------")
    print(final_output)
    print("-----------------------------------")
