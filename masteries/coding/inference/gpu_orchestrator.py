"""
PACE GPU Orchestrator Node
Task LE-3: Ensemble pipeline running Actor and Critic sequentially on an 8GB RTX GPU.
"""

import torch
from masteries.coding.inference.actor_generate import generate_fixes
from masteries.coding.inference.critic_predict import evaluate_syntax_batch


def run_ensemble_pipeline():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[SYSTEM] Active Device: {device}")
    print(
        f"[VRAM] Initial Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
    )

    # The prompt that caused the hallucination in testing
    test_prompt = "def fibonacci(n):"

    print("\n--- [PHASE 1] INITIATING ACTOR GENERATION ---")

    # Generate 3 candidates
    candidate_fixes = generate_fixes(test_prompt, num_return_sequences=3)

    for i, fix in enumerate(candidate_fixes):
        print(f"\n[ACTOR CANDIDATE {i+1}]:\n{fix}")

    print(
        f"\n[VRAM] Mid-point Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
    )

    print("\n--- [PHASE 2] INITIATING CRITIC VALIDATION ---")

    # Score all 3 candidates
    bug_probabilities = evaluate_syntax_batch(candidate_fixes)

    for i, score in enumerate(bug_probabilities):
        print(f"[CRITIC SCORE {i+1}]: {score:.4f} (Probability of being a Bug)")

    # Select the winning code (Lowest probability of being a bug)
    best_index = bug_probabilities.index(min(bug_probabilities))
    best_code = candidate_fixes[best_index]

    print("\n==========================================")
    print(" 🏆 ENSEMBLE WINNER (Safest Code)")
    print("==========================================")
    print(best_code)
    print("==========================================")

    print(
        f"\n[VRAM] Final Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
    )
    print("[SUCCESS] Sequential Hardware Routing Complete.")


if __name__ == "__main__":
    run_ensemble_pipeline()
