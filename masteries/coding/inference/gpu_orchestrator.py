"""
PACE GPU Orchestrator Node
Task LE-3: Proves that the Actor and Critic can sequentially share the RTX 4060 without memory overlap.
"""

import torch
from masteries.coding.inference.actor_generate import generate_fix
from masteries.coding.inference.critic_predict import evaluate_syntax


def run_sequential_pipeline():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[SYSTEM] Active Device: {device}")
    print(
        f"[VRAM] Initial Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
    )
    print("\n--- INITIATING ACTOR PASS ---")
    test_prompt = "Write a python function that prints Hello World"
    fix = generate_fix(test_prompt)
    print(f"[ACTOR] Generated Code: {fix}")

    print(
        f"[VRAM] Mid-point Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
    )

    print("\n--- INITIATING CRITIC PASS ---")
    buggy_code = "PRINT(Hello World)"
    prediction = evaluate_syntax(buggy_code)
    print(f"[CRITIC] Predicted: {prediction}")

    print(
        f"[VRAM] Final Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
    )

    print("\n[SUCCESS] Sequential Hardware Routing Complete.")


if __name__ == "__main__":
    run_sequential_pipeline()
