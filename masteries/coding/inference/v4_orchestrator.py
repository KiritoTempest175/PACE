import time
import gc
import sys
import os
import torch

# Add paths to the actor and critic modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'training', 'actor')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'training', 'critic')))

from alt_actor_model import ActorModel
from alt_critic_model import QwenCritic

# Global instances to avoid reloading models on every request
_actor = None
_critic = None

def get_actor():
    global _actor
    if _actor is None:
        print("Initializing Actor Model...")
        _actor = ActorModel()
    return _actor

def get_critic():
    global _critic
    if _critic is None:
        print("Initializing Critic Model...")
        _critic = QwenCritic()
    return _critic

def flush_vram():
    """Forces PyTorch to release memory back to the OS."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def v4_pipeline(user_prompt, max_iterations=1, speed_mode="pro"):
    """
    PACE Dual-Engine Orchestrator.
    Uses the Actor (3B) to generate code and Critic (1.5B) to review and revise.
    """
    yield {"type": "status", "content": f"Initializing Actor-Critic Ensemble (v4 - {speed_mode} mode)..."}
    
    # Load models
    actor = get_actor()
    if speed_mode == "pro":
        critic = get_critic()
    
    yield {"type": "status", "content": "Actor is generating initial code..."}
    
    # Generate initial code
    code_snippet = ""
    for token in actor.generate_code(user_prompt):
        code_snippet += token
        yield {"type": "token", "content": token}
        
    # Clear CUDA cache after Actor completes generation
    flush_vram()
        
    if speed_mode == "pro":
        for i in range(max_iterations):
            yield {"type": "status", "content": f"Critic is analyzing the code (Iteration {i+1})..."}
            
            # Critique the generated code
            critique = critic.critique(code_snippet, context=user_prompt)
            print(f"\n--- CRITIQUE (Iteration {i+1}) ---\n{critique}\n-----------------------------\n")
            
            # Clear CUDA cache after Critic completes analysis
            flush_vram()
            
            # Check if critic is satisfied (basic heuristic)
            lower_critique = critique.lower()
            if "looks good" in lower_critique or "no issues" in lower_critique or "no bugs" in lower_critique or "is correct" in lower_critique:
                yield {"type": "status", "content": "Critic approved the code!"}
                break
                
            yield {"type": "status", "content": f"Critic found issues. Actor is revising (Iteration {i+1})..."}
            yield {"type": "clear"}  # Clear the chat window for the revised code
            
            new_code_snippet = ""
            for token in actor.revise_code(user_prompt, code_snippet, critique):
                new_code_snippet += token
                yield {"type": "token", "content": token}
                
            code_snippet = new_code_snippet
            
            # Clear CUDA cache after Actor completes revision
            flush_vram()
            
    yield {"type": "status", "content": "Ensemble Pipeline Complete."}


# Alias for backward compatibility / streaming callers
v4_stream_pipeline = v4_pipeline


if __name__ == "__main__":
    print("Testing v4_pipeline directly...")
    test_prompt = "Write a Python function to calculate the factorial of a number."
    
    for event in v4_pipeline(test_prompt):
        if event["type"] == "token":
            import sys
            sys.stdout.write(event["content"])
            sys.stdout.flush()
        elif event["type"] == "status":
            print(f"\n[STATUS] {event['content']}")
        elif event["type"] == "clear":
            print("\n[CLEAR] (Actor is revising...)")
    print("\n\nTest execution finished.")
