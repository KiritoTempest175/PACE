import gc
import sys
import torch

from masteries.research.training.actor.alt_actor_model import ResearchActorModel
from masteries.research.training.critic.alt_critic_model import ResearchCriticModel

# Global instances to avoid reloading models on every request
_actor = None
_critic = None


def get_actor():
    global _actor
    if _actor is None:
        print("Initializing Research Actor Model...")
        _actor = ResearchActorModel()
    return _actor


def get_critic():
    global _critic
    if _critic is None:
        print("Initializing Research Critic Model...")
        _critic = ResearchCriticModel()
    return _critic


def flush_vram():
    """Forces PyTorch to release memory back to the OS."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def research_pipeline(user_prompt, max_iterations=1, speed_mode="pro"):
    """
    PACE Research Orchestrator.
    Uses the Actor (4B) to generate synthesis and Critic (2B) to review and revise.
    """
    yield {
        "type": "status",
        "content": f"Initializing Research Actor-Critic Ensemble ({speed_mode} mode)...",
    }

    # Load models
    actor = get_actor()
    if speed_mode == "pro":
        critic = get_critic()

    yield {"type": "status", "content": "Actor is synthesizing research..."}

    # Generate initial text
    text_snippet = ""
    for token in actor.generate_research(user_prompt):
        text_snippet += token
        yield {"type": "token", "content": token}

    # Clear CUDA cache after Actor completes generation
    flush_vram()

    if speed_mode == "pro":
        for i in range(max_iterations):
            yield {
                "type": "status",
                "content": f"Critic is auditing citations and logic (Iteration {i+1})...",
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
                or "satisfactory" in lower_critique
            ):
                yield {"type": "status", "content": "Critic approved the synthesis!"}
                break

            yield {
                "type": "status",
                "content": f"Critic found improvements. Actor is revising (Iteration {i+1})...",
            }
            yield {"type": "clear"}  # Clear the chat window for the revised text

            new_text_snippet = ""
            for token in actor.revise_research(user_prompt, text_snippet, critique):
                new_text_snippet += token
                yield {"type": "token", "content": token}

            text_snippet = new_text_snippet

            # Clear CUDA cache after Actor completes revision
            flush_vram()

    yield {"type": "status", "content": "Research Pipeline Complete."}


if __name__ == "__main__":
    print("Testing research_pipeline directly...")
    test_prompt = "Explain the difference between LSTMs and Transformers."

    for event in research_pipeline(test_prompt):
        if event["type"] == "token":
            import sys

            sys.stdout.write(event["content"])
            sys.stdout.flush()
        elif event["type"] == "status":
            print(f"\n[STATUS] {event['content']}")
        elif event["type"] == "clear":
            print("\n[CLEAR] (Actor is revising...)")
    print("\n\nTest execution finished.")
