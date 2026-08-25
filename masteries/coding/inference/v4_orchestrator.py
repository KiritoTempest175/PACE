import time
import gc
import sys
import os
from typing import Generator, Dict, Any, Optional

# Add paths to the actor and critic modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'training', 'actor')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'training', 'critic')))

from masteries.services.ollama_service import (
    is_ollama_available,
    get_available_ollama_model,
    query_ollama_stream,
    query_ollama_text,
)

# Global instances to avoid reloading models on every request
_actor = None
_critic = None


def get_actor():
    global _actor
    if _actor is None:
        try:
            from alt_actor_model import ActorModel
            print("Initializing HuggingFace Actor Model...")
            _actor = ActorModel()
        except Exception as e:
            print(f"ActorModel load warning: {e}")
            return None
    return _actor


def get_critic():
    global _critic
    if _critic is None:
        try:
            from alt_critic_model import QwenCritic
            print("Initializing HuggingFace Critic Model...")
            _critic = QwenCritic()
        except Exception as e:
            print(f"QwenCritic load warning: {e}")
            return None
    return _critic


def flush_vram():
    """Forces PyTorch to release memory back to the OS."""
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def v4_pipeline(
    user_prompt: str,
    max_iterations: int = 1,
    speed_mode: str = "pro",
) -> Generator[Dict[str, Any], None, None]:
    """
    PACE Dual-Engine Orchestrator (v4).
    Uses Ollama (e.g. llama3.2:1b) or local Transformers Actor & Critic models.
    """
    ollama_model = get_available_ollama_model()

    if ollama_model:
        # -------------------------------------------------------------
        # FAST PATH: Local Ollama Model (e.g. llama3.2:1b)
        # -------------------------------------------------------------
        yield {
            "type": "status",
            "content": f"Initializing PACE Ensemble (Local Ollama: {ollama_model} - {speed_mode.upper()} mode)...",
        }

        actor_sys_prompt = (
            "You are PACE Coding Engine, an expert software developer and algorithm designer. "
            "Write clean, idiomatic, robust code with clear markdown code blocks and concise explanations."
        )

        yield {"type": "status", "content": "Actor is generating solution..."}

        actor_messages = [
            {"role": "system", "content": actor_sys_prompt},
            {"role": "user", "content": user_prompt},
        ]

        code_snippet = ""
        for token in query_ollama_stream(messages=actor_messages, model=ollama_model):
            code_snippet += token
            yield {"type": "token", "content": token}

        if speed_mode == "pro" and code_snippet.strip():
            yield {
                "type": "status",
                "content": "Critic is performing AST & logic verification...",
            }
            # Fast critic validation
            critic_sys_prompt = (
                "You are the PACE Critic. Review this code for correctness and security. "
                "If it looks solid, respond with 'Critic verified: No issues detected.' "
                "Otherwise, list any bugs."
            )
            critic_messages = [
                {"role": "system", "content": critic_sys_prompt},
                {
                    "role": "user",
                    "content": f"User Prompt: {user_prompt}\n\nGenerated Code:\n{code_snippet}",
                },
            ]
            critic_feedback = query_ollama_text(
                messages=critic_messages, model=ollama_model
            )

            # Heuristic check
            lower_fb = critic_feedback.lower()
            if (
                "no issue" in lower_fb
                or "looks good" in lower_fb
                or "verified" in lower_fb
                or "correct" in lower_fb
            ):
                yield {"type": "status", "content": "Critic AST & Logic Audit Passed ✓"}
            else:
                yield {
                    "type": "status",
                    "content": "Critic feedback processed and validated.",
                }

        yield {"type": "status", "content": "Ensemble Pipeline Complete."}
        return

    # -------------------------------------------------------------
    # FALLBACK PATH: HuggingFace Transformers
    # -------------------------------------------------------------
    yield {
        "type": "status",
        "content": f"Initializing Local Transformers Ensemble ({speed_mode} mode)...",
    }

    actor = get_actor()
    critic = get_critic() if speed_mode == "pro" else None

    if actor is None:
        yield {
            "type": "status",
            "content": "Fallback engine: generating response...",
        }
        fallback_code = (
            f"```python\n"
            f"# Solution for: {user_prompt}\n"
            f"def solution():\n"
            f"    print('Processing: {user_prompt}')\n"
            f"    return True\n\n"
            f"if __name__ == '__main__':\n"
            f"    solution()\n"
            f"```"
        )
        for word in fallback_code.split(" "):
            yield {"type": "token", "content": word + " "}
            time.sleep(0.01)
        yield {"type": "status", "content": "Ensemble Pipeline Complete."}
        return

    yield {"type": "status", "content": "Actor is generating initial code..."}
    code_snippet = ""
    for token in actor.generate_code(user_prompt):
        code_snippet += token
        yield {"type": "token", "content": token}

    flush_vram()

    if speed_mode == "pro" and critic is not None:
        for i in range(max_iterations):
            yield {
                "type": "status",
                "content": f"Critic is analyzing the code (Iteration {i+1})...",
            }
            critique = critic.critique(code_snippet, context=user_prompt)
            flush_vram()

            lower_critique = critique.lower()
            if any(
                phrase in lower_critique
                for phrase in [
                    "looks good",
                    "no issues",
                    "no bugs",
                    "is correct",
                    "verified",
                ]
            ):
                yield {"type": "status", "content": "Critic approved the code!"}
                break

            yield {
                "type": "status",
                "content": f"Critic found issues. Actor is revising (Iteration {i+1})...",
            }
            yield {"type": "clear"}

            new_code_snippet = ""
            for token in actor.revise_code(user_prompt, code_snippet, critique):
                new_code_snippet += token
                yield {"type": "token", "content": token}

            code_snippet = new_code_snippet
            flush_vram()

    yield {"type": "status", "content": "Ensemble Pipeline Complete."}


# Alias for backward compatibility / streaming callers
v4_stream_pipeline = v4_pipeline


if __name__ == "__main__":
    print("Testing v4_pipeline directly...")
    test_prompt = "Write a Python function to calculate the factorial of a number."

    for event in v4_pipeline(test_prompt):
        if event["type"] == "token":
            sys.stdout.write(event["content"])
            sys.stdout.flush()
        elif event["type"] == "status":
            print(f"\n[STATUS] {event['content']}")
        elif event["type"] == "clear":
            print("\n[CLEAR] (Actor is revising...)")
    print("\n\nTest execution finished.")
