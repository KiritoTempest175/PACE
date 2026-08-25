import os
import json
from typing import Generator, Dict, Any, Optional

from masteries.coding.training.actor.alt_actor_model import ActorModel
from masteries.services.ollama_service import (
    query_ollama_stream,
    query_ollama_text,
    is_ollama_available,
    DEFAULT_OLLAMA_MODEL,
)

# Configuration defaults
DEFAULT_MODEL = os.getenv("PACE_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)



def generate_text_ollama(
    system_msg: str, user_msg: str, model: str = DEFAULT_MODEL
) -> Generator[str, None, None]:
    """Helper to stream text from Ollama using chat format."""
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    for chunk in query_ollama_stream(messages=messages, model=model):
        yield chunk


def generate_text_transformers(
    tokenizer, model, system_msg: str, user_msg: str, device, max_tokens: int = 1024
) -> Generator[str, None, None]:
    """Fallback helper to stream text from HuggingFace Transformers."""
    from transformers import TextIteratorStreamer
    from threading import Thread

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template is not None:
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    else:
        text = f"{system_msg}\n\n{user_msg}\n\nAssistant:"

    model_inputs = tokenizer([text], return_tensors="pt").to(device)
    streamer = TextIteratorStreamer(
        tokenizer, skip_prompt=True, skip_special_tokens=True
    )

    generation_kwargs = dict(
        **model_inputs,
        max_new_tokens=max_tokens,
        do_sample=True,
        temperature=0.3,
        streamer=streamer,
    )

    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    for new_text in streamer:
        yield new_text


def v3_pipeline(
    user_prompt: str,
    max_iterations: int = 3,
    backend: str = "ollama",
    model: str = DEFAULT_MODEL,
) -> Generator[Dict[str, Any], None, None]:
    """
    Pipelined Actor-Critic Ensemble Orchestrator.
    Executes:
      1. Critic Prompt Expansion & Reasoning Blueprint
      2. Actor Initial Code Generation (Streamed)
      3. Critic Evaluation & Verification Loop
      4. Actor Revision / Refinement (Streamed)
    """
    print(f"=== STARTING V3 ORCHESTRATOR PIPELINE [{backend.upper()}: {model}] ===")

    # ---------------------------------------------------------
    # PHASE 1: Critic expands user prompt to give Actor context
    # ---------------------------------------------------------
    sys_expand = "You are an expert Software Architect."
    usr_expand = (
        f"A user has requested the following code/feature: '{user_prompt}'\n\n"
        f"Please write a concise, highly detailed instruction prompt for a developer to implement this. "
        f"CRITICAL INSTRUCTION: Instruct the developer to include step-by-step logic in code comments. "
        f"Output ONLY the prompt to give to the developer, nothing else."
    )

    print("\n[CRITIC] Generating detailed prompt for Actor...")
    yield {"type": "status", "content": "Critic analyzing requirements..."}

    actor_instructions_chunks = []
    try:
        for chunk in generate_text_ollama(sys_expand, usr_expand, model=model):
            actor_instructions_chunks.append(chunk)
    except Exception as e:
        print(f"[CRITIC] Direct Ollama call failed: {e}. Using prompt directly.")
        actor_instructions_chunks = [user_prompt]

    actor_instructions = "".join(actor_instructions_chunks).strip() or user_prompt
    print(f"\n--- Critic's Expanded Prompt ---\n{actor_instructions}\n--------------------------------")

    # ---------------------------------------------------------
    # PHASE 2: Actor Generates Initial Code
    # ---------------------------------------------------------
    actor = ActorModel(model_id=model, backend=backend)

    print("\n[ACTOR] Generating initial code...")
    yield {"type": "status", "content": "Actor writing initial code..."}
    yield {"type": "clear"}

    current_code_chunks = []
    for chunk in actor.generate_code(actor_instructions):
        current_code_chunks.append(chunk)
        yield {"type": "token", "content": chunk}

    current_code = "".join(current_code_chunks)
    print(f"\n--- Actor's Initial Code ---\n{current_code}\n----------------------------")

    # ---------------------------------------------------------
    # PHASE 3: Refinement Loop (Critic evaluates, Actor fixes)
    # ---------------------------------------------------------
    iteration = 1
    while iteration <= max_iterations:
        print(f"\n=== REFINEMENT ITERATION {iteration} ===")
        yield {
            "type": "status",
            "content": f"Iteration {iteration}: Critic evaluating code...",
        }

        sys_eval = "You are an expert Code Critic AI."
        usr_eval = (
            f"The original user requirement is: '{user_prompt}'\n\n"
            f"The developer wrote the following code:\n```python\n{current_code}\n```\n\n"
            f"Please review this code for bugs, logic flaws, or missing edge cases. "
            f"If it is correct, clean, and fulfills the requirement, START your response exactly with: 'CODE_IS_PERFECT'.\n"
            f"Otherwise, explain specifically what to fix."
        )

        print("\n[CRITIC] Evaluating code...")
        critic_feedback_chunks = []
        try:
            for chunk in generate_text_ollama(sys_eval, usr_eval, model=model):
                critic_feedback_chunks.append(chunk)
        except Exception as e:
            print(f"[CRITIC] Evaluation error: {e}")
            critic_feedback_chunks = ["CODE_IS_PERFECT"]

        critic_feedback = "".join(critic_feedback_chunks).strip()
        print(f"\n--- Critic's Feedback ---\n{critic_feedback}\n-------------------------")

        # Check if the Critic approved the code
        if "CODE_IS_PERFECT" in critic_feedback.upper() or critic_feedback.upper().startswith("CODE_IS_PERFECT"):
            print("\n[SUCCESS] Critic approved the code!")
            yield {"type": "status", "content": "Critic approved the code!"}
            break

        if iteration == max_iterations:
            print("\n[INFO] Max refinement iterations reached. Generating final polished version.")
            yield {
                "type": "status",
                "content": "Max iterations reached. Generating final code...",
            }

            sys_final = "You are an expert Software Engineer."
            usr_final = (
                f"Please provide the complete, finalized Python code for: '{user_prompt}'. "
                f"Ensure clean structure, comments, and bug-free implementation."
            )

            yield {"type": "clear"}
            critic_correct_code_chunks = []
            try:
                for chunk in generate_text_ollama(sys_final, usr_final, model=model):
                    critic_correct_code_chunks.append(chunk)
                    yield {"type": "token", "content": chunk}
                current_code = "".join(critic_correct_code_chunks)
            except Exception as e:
                print(f"[FINAL] Generation error: {e}")

            # Save to continuous learning dataset
            dataset_path = "masteries/coding/data/continuous_learning.jsonl"
            try:
                os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
                with open(dataset_path, "a", encoding="utf-8") as f:
                    f.write(
                        json.dumps({"prompt": user_prompt, "target_code": current_code})
                        + "\n"
                    )
            except Exception:
                pass
            break

        # Load Actor for Refinement
        print(f"\n[ACTOR] Refining code based on iteration {iteration} feedback...")
        yield {
            "type": "status",
            "content": f"Iteration {iteration}: Actor refining code...",
        }
        yield {"type": "clear"}

        current_code_chunks = []
        for chunk in actor.revise_code(user_prompt, current_code, critic_feedback):
            current_code_chunks.append(chunk)
            yield {"type": "token", "content": chunk}
        current_code = "".join(current_code_chunks)

        iteration += 1

    print("\n\n==========================================")
    print(" [SUCCESS] FINAL ENSEMBLE OUTPUT")
    print("==========================================")
    print(current_code)
    print("==========================================")


if __name__ == "__main__":
    test_user_prompt = "Write a Python function to find prime numbers up to n using sieve of Eratosthenes."
    for event in v3_pipeline(test_user_prompt, model=DEFAULT_MODEL):
        if event["type"] == "token":
            print(event["content"], end="", flush=True)
        elif event["type"] == "status":
            print("\n[" + event["content"] + "]")

