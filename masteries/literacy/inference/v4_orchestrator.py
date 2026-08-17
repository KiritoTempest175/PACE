import gc
import sys
import torch

from masteries.literacy.training.actor.alt_actor_model import LiteracyActorModel
from masteries.literacy.training.critic.alt_critic_model import LiteracyCriticModel

# Global instances to avoid reloading models on every request
_actor = None
_critic = None


def get_actor():
    global _actor
    if _actor is None:
        print("Initializing Literacy Actor Model...")
        _actor = LiteracyActorModel()
    return _actor


def get_critic():
    global _critic
    if _critic is None:
        print("Initializing Literacy Critic Model...")
        _critic = LiteracyCriticModel()
    return _critic


def flush_vram():
    """Forces PyTorch to release memory back to the OS."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def literacy_pipeline(user_prompt, max_iterations=1, speed_mode="pro"):
    """
    PACE Literacy Orchestrator.
    Uses the Actor (4B) to generate text and Critic (2B) to review and revise.
    """
    yield {
        "type": "status",
        "content": f"Initializing Literacy Actor-Critic Ensemble ({speed_mode} mode)...",
    }

    # Load models
    actor = get_actor()
    if speed_mode == "pro":
        critic = get_critic()

    yield {"type": "status", "content": "Actor is synthesizing text..."}

    # Generate initial text
    text_snippet = ""
    for token in actor.generate_text(user_prompt):
        text_snippet += token
        yield {"type": "token", "content": token}

    # Clear CUDA cache after Actor completes generation
    flush_vram()

    if speed_mode == "pro":
        for i in range(max_iterations):
            yield {
                "type": "status",
                "content": f"Critic is analyzing the logic and flow (Iteration {i+1})...",
            }

            # Critique the generated text
            print(f"\n--- CRITIQUE (Iteration {i+1}) ---")
            critique = ""
            for token in critic.critique(text_snippet, context=user_prompt):
                critique += token
                print(token, end="", flush=True)
            print("\n-----------------------------\n")

            # Clear CUDA cache after Critic completes analysis
            flush_vram()

            # Check if critic is satisfied (basic heuristic)
            lower_critique = critique.lower()
            if (
                "looks good" in lower_critique
                or "no issues" in lower_critique
                or "is well written" in lower_critique
                or "is factual" in lower_critique
                or "accurate" in lower_critique
            ):
                yield {"type": "status", "content": "Critic approved the content!"}
                break

            yield {
                "type": "status",
                "content": f"Critic found improvements. Actor is revising (Iteration {i+1})...",
            }
            yield {"type": "clear"}  # Clear the chat window for the revised text

            new_text_snippet = ""
            for token in actor.revise_text(user_prompt, text_snippet, critique):
                new_text_snippet += token
                yield {"type": "token", "content": token}

            text_snippet = new_text_snippet

            # Clear CUDA cache after Actor completes revision
            flush_vram()

    yield {"type": "status", "content": "Literacy Pipeline Complete."}


if __name__ == "__main__":
    print("Testing literacy_pipeline directly...")
    test_prompt = "Explain quantum computing to a 10 year old."

    for event in literacy_pipeline(test_prompt):
        if event["type"] == "token":
            import sys

            sys.stdout.write(event["content"])
            sys.stdout.flush()
        elif event["type"] == "status":
            print(f"\n[STATUS] {event['content']}")
        elif event["type"] == "clear":
            print("\n[CLEAR] (Actor is revising...)")
    print("\n\nTest execution finished.")
