import torch
import gc
import os

from transformers import AutoTokenizer, AutoModelForCausalLM

# Hardware Settings
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model Paths
# Using the standard Actor model from V1/V2 and the new Qwen 3B model as the Critic
ACTOR_PATH = "masteries/coding/models/actor_v1"
CRITIC_PATH = "Qwen/Qwen2.5-3B-Instruct"


def flush_vram():
    """Forces PyTorch to release memory back to the OS."""
    gc.collect()
    torch.cuda.empty_cache()


def load_actor():
    print("\n[VRAM] Loading Actor Model...")
    # Add error handling in case actor_v1 isn't fully downloaded in this env
    try:
        tokenizer = AutoTokenizer.from_pretrained(ACTOR_PATH)
        model = AutoModelForCausalLM.from_pretrained(
            ACTOR_PATH,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        )
        model.to(device)
        return tokenizer, model
    except Exception as e:
        print(
            f"[WARNING] Could not load Actor from {ACTOR_PATH}. Using Qwen 3B as Actor fallback for testing: {e}"
        )
        tokenizer = AutoTokenizer.from_pretrained(CRITIC_PATH)
        model = AutoModelForCausalLM.from_pretrained(
            CRITIC_PATH,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        )
        model.to(device)
        return tokenizer, model


def load_critic():
    print("\n[VRAM] Loading Critic Model (Qwen 3B)...")
    tokenizer = AutoTokenizer.from_pretrained(CRITIC_PATH)
    model = AutoModelForCausalLM.from_pretrained(
        CRITIC_PATH,
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
    )
    model.to(device)
    return tokenizer, model


def generate_text(tokenizer, model, system_msg, user_msg, max_tokens=1024):
    """Helper function to generate text using Chat Templates."""
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    # Check if the tokenizer has a chat template, otherwise do manual formatting
    if (
        hasattr(tokenizer, "apply_chat_template")
        and tokenizer.chat_template is not None
    ):
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    else:
        text = f"{system_msg}\n\n{user_msg}\n\nAssistant:"

    model_inputs = tokenizer([text], return_tensors="pt").to(device)

    with torch.no_grad():
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=0.3,
        )

    generated_ids = [
        output_ids[len(input_ids) :]
        for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response


def v3_pipeline(user_prompt, max_iterations=3):
    print("=== STARTING V3 ORCHESTRATOR PIPELINE ===")

    # ---------------------------------------------------------
    # PHASE 1: Critic expands user prompt to give Actor context
    # ---------------------------------------------------------
    critic_tok, critic_mod = load_critic()

    sys_expand = "You are an expert Software Architect."
    usr_expand = (
        f"A user has requested the following code/feature: '{user_prompt}'\n\n"
        f"Please write a highly detailed instruction prompt for a developer to implement this. "
        f"CRITICAL INSTRUCTION: You MUST instruct the developer to write their reasoning and logic planning inside python comments "
        f"(e.g., # Step 1: ...) before writing any actual code. This ensures there are no loopholes or logical errors. "
        f"Output ONLY the prompt to give to the developer, nothing else."
    )

    print("\n[CRITIC] Generating detailed prompt for Actor...")
    actor_instructions = generate_text(
        critic_tok, critic_mod, sys_expand, usr_expand, max_tokens=512
    )
    print(
        f"\n--- Critic's Expanded Prompt ---\n{actor_instructions}\n--------------------------------"
    )

    del critic_tok, critic_mod
    flush_vram()

    # ---------------------------------------------------------
    # PHASE 2: Actor Generates Initial Code
    # ---------------------------------------------------------
    actor_tok, actor_mod = load_actor()

    sys_actor = "You are an expert Python Developer. You follow instructions perfectly."
    usr_actor = actor_instructions

    print("\n[ACTOR] Generating initial code (incorporating reasoning in comments)...")
    current_code = generate_text(
        actor_tok, actor_mod, sys_actor, usr_actor, max_tokens=1024
    )
    print(
        f"\n--- Actor's Initial Code ---\n{current_code}\n----------------------------"
    )

    del actor_tok, actor_mod
    flush_vram()

    # ---------------------------------------------------------
    # PHASE 3: Refinement Loop (Critic evaluates, Actor fixes)
    # ---------------------------------------------------------
    iteration = 1
    while iteration <= max_iterations:
        print(f"\n=== REFINEMENT ITERATION {iteration} ===")

        # Load Critic
        critic_tok, critic_mod = load_critic()

        sys_eval = "You are an expert Code Critic AI."
        usr_eval = (
            f"The original user requirement is: '{user_prompt}'\n\n"
            f"The developer wrote the following code:\n```python\n{current_code}\n```\n\n"
            f"Please review this code for bugs and logic flaws. Does it perfectly meet the requirements and contain zero bugs?\n"
            f"If it is perfect and logically sound, START your response exactly with the word: 'CODE_IS_PERFECT'.\n"
            f"If it is not perfect, DO NOT start with 'CODE_IS_PERFECT'. Instead, provide a very specific, actionable prompt instructing the developer on exactly what to fix and how to rewrite it."
        )

        print("\n[CRITIC] Evaluating code...")
        critic_feedback = generate_text(
            critic_tok, critic_mod, sys_eval, usr_eval, max_tokens=512
        )
        print(
            f"\n--- Critic's Feedback ---\n{critic_feedback}\n-------------------------"
        )

        del critic_tok, critic_mod
        flush_vram()

        # Check if the Critic approved the code (strict check)
        if critic_feedback.strip().upper().startswith("CODE_IS_PERFECT"):
            print("\n[SUCCESS] Critic approved the code!")
            break

        if iteration == max_iterations:
            print(
                "\n[WARNING] Max iterations reached without Critic approval. Using Critic for final fallback."
            )

            # Use Critic to generate correct code
            sys_final = "You are an expert Python Developer."
            usr_final = f"The developer failed to write the code for: '{user_prompt}'. Please provide the complete, correct Python code for this prompt. DO NOT use markdown code blocks, just output the raw python code."

            print("\n[CRITIC] Generating correct code for continuous learning...")
            critic_tok, critic_mod = load_critic()
            critic_correct_code = generate_text(
                critic_tok, critic_mod, sys_final, usr_final, max_tokens=1024
            )

            del critic_tok, critic_mod
            flush_vram()

            # Clean up potential markdown blocks if the critic still included them
            clean_code = (
                critic_correct_code.replace("```python", "").replace("```", "").strip()
            )

            # Prepend the required comment
            current_code = f"# Generated by Critic due to Actor failure\n{clean_code}"

            # Save to continuous learning dataset
            dataset_path = "masteries/coding/data/continuous_learning.jsonl"
            os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
            try:
                import json

                with open(dataset_path, "a") as f:
                    f.write(
                        json.dumps({"prompt": user_prompt, "target_code": current_code})
                        + "\n"
                    )
                print(
                    f"[DATASET] Added failure case to {dataset_path} for continuous learning."
                )
            except Exception as e:
                print(f"[WARNING] Failed to save dataset: {e}")

            break

        # Load Actor for Refinement
        actor_tok, actor_mod = load_actor()

        sys_refine = "You are an expert Python Developer."
        usr_refine = (
            f"You previously wrote this code for the task '{user_prompt}':\n```python\n{current_code}\n```\n\n"
            f"An expert Code Critic reviewed it and provided this feedback:\n{critic_feedback}\n\n"
            f"Please rewrite the code completely to address ALL of the critic's feedback. "
            f"Remember to include your logic reasoning in comments to avoid loopholes before writing the code."
        )

        print("\n[ACTOR] Refining code based on Critic's feedback...")
        current_code = generate_text(
            actor_tok, actor_mod, sys_refine, usr_refine, max_tokens=1024
        )
        print(
            f"\n--- Actor's Refined Code ---\n{current_code}\n----------------------------"
        )

        del actor_tok, actor_mod
        flush_vram()

        iteration += 1

    print("\n\n==========================================")
    print(" 🏆 FINAL ENSEMBLE OUTPUT")
    print("==========================================")
    print(current_code)
    print("==========================================")

    return current_code


if __name__ == "__main__":
    test_user_prompt = "Write a Python code to search 19 in this array 10,16,19,30,41,52. use linear search and return index number."
    v3_pipeline(test_user_prompt)
