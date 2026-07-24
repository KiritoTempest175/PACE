"""
PACE GPU Orchestrator Node
Task LE-3: Proves that the Actor and Critic can sequentially share the RTX 4060 without memory overlap.
"""

# IMPORT REQUIRED LIBRARIES
# Import torch
# Import generate_fix from masteries.coding.inference.actor_generate
# Import evaluate_syntax from masteries.coding.inference.critic_predict

import torch
from masteries.coding.inference.actor_generate import generate_fix
from masteries.coding.inference.critic_predict import evaluate_syntax


def run_sequential_pipeline():
    # ==========================================
    # 1. INITIAL STATE
    # ==========================================
    # Check if CUDA is available.
    # Print the starting VRAM allocated in MB. (It should be near 0 MB).
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[SYSTEM] Active Device: {device}")
    print(
        f"[VRAM] Initial Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
    )
    # ==========================================
    # 2. ACTOR EXECUTION
    # ==========================================
    print("\n--- INITIATING ACTOR PASS ---")
    # Define a test prompt (e.g., "Write a python function that prints Hello World").
    # Call generate_fix() with your prompt.
    # Print the Actor's output string.
    test_prompt = "Write a python function that prints Hello World"
    fix = generate_fix(test_prompt)
    print(f"[ACTOR] Generated Code: {fix}")

    # ==========================================
    # 3. MID-POINT VRAM CHECK
    # ==========================================
    # Print the current VRAM allocated in MB.
    # (If your Teardown Protocol from LE-1 worked, this MUST be near 0 MB.
    # If it is 3000+ MB, the Critic will crash the system in the next step!)
    print(
        f"[VRAM] Mid-point Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
    )

    # ==========================================
    # 4. CRITIC EXECUTION
    # ==========================================
    print("\n--- INITIATING CRITIC PASS ---")
    # Define a buggy string of Python code (e.g., "def bad_function() return False")
    # Call evaluate_syntax() with your buggy code.
    # Print the Critic's integer prediction.
    buggy_code = "PRINT(Hello World)"
    prediction = evaluate_syntax(buggy_code)
    print(f"[CRITIC] Predicted: {prediction}")

    # ==========================================
    # 5. FINAL VRAM CHECK
    # ==========================================
    # Print the final VRAM allocated in MB.
    print(
        f"[VRAM] Final Allocation: {torch.cuda.memory_allocated() / (1024**2):.2f} MB"
    )

    print("\n[SUCCESS] Sequential Hardware Routing Complete.")


# =====================================================================
# SYSTEM TEST ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    run_sequential_pipeline()
