import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread


class ActorModel:
    """
    A Code Actor model using an 8B local LLM (e.g., Llama-3.1-8B-Instruct)
    to generate and revise code based on user prompts and critiques.
    """

    def __init__(
        self,
        model_id="Qwen/Qwen2.5-Coder-7B-Instruct",
        device="cuda" if torch.cuda.is_available() else "cpu",
    ):
        self.device = device
        self.model_id = model_id
        print(f"Loading tokenizer from {model_id}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

        print(f"Loading model {model_id} to {self.device}...")
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        self.model.to(device)

        print("Actor Model loaded successfully.")

    def generate_code(self, prompt: str) -> str:
        """
        Understand the user prompt and generate code.

        Args:
            prompt (str): The user requirement or task.

        Returns:
            str: The generated code.
        """
        system_prompt = (
            "You are an expert software developer. Your task is to write high-quality, "
            "efficient, and bug-free code based on the user's requirements. "
            "Provide only the code within markdown code blocks."
        )

        user_prompt = f"Please write code to fulfill the following requirement:\n\n{prompt}\n\nProvide the code:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        # Add a streamer to see the output generated in real-time
        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        generation_kwargs = dict(
            **model_inputs,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.7,
            streamer=streamer,
        )

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        for new_text in streamer:
            yield new_text

    def revise_code(self, prompt: str, original_code: str, critique: str) -> str:
        """
        Understand the critic prompt/critique and revise the code.

        Args:
            prompt (str): The original user requirement.
            original_code (str): The code that had errors.
            critique (str): The feedback from the critic model.

        Returns:
            str: The revised code.
        """
        system_prompt = (
            "You are an expert software developer. You previously wrote some code that was reviewed "
            "by a Code Critic. The critic found errors or areas for improvement. Your task is to "
            "understand the critique and revise the code accordingly. Provide the revised code "
            "within markdown code blocks."
        )

        user_prompt = (
            f"Original Requirement:\n{prompt}\n\n"
            f"Original Code:\n```python\n{original_code}\n```\n\n"
            f"Critic Feedback:\n{critique}\n\n"
            "Please revise the code to address the critic's feedback. Provide the updated code:"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        # Add a streamer to see the output generated in real-time
        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        generation_kwargs = dict(
            **model_inputs,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.5,  # Lower temperature for revision to keep it focused
            streamer=streamer,
        )

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        for new_text in streamer:
            yield new_text


if __name__ == "__main__":
    print(
        "Initializing Actor Model (this may take a while as it downloads the 7B model weights)..."
    )
    actor = ActorModel()

    task_prompt = "Write a Python function to calculate the Fibonacci sequence up to n."

    print("\n--- GENERATING CODE ---")
    generated = actor.generate_code(task_prompt)
    print(generated)

    print("\n--- REVISING CODE ---")
    mock_critique = "The code uses a slow recursive approach. Please use an iterative approach or memoization to improve performance."
    revised = actor.revise_code(task_prompt, generated, mock_critique)
    print(revised)
