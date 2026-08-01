import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class QwenCritic:
    """
    A Code Critic model using Qwen 3B to check for both bugs and logic.
    """

    def __init__(
        self,
        model_id="Qwen/Qwen2.5-3B-Instruct",
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

        print("Model loaded successfully.")

    def critique(self, code: str, context: str = "") -> str:
        """
        Evaluate the provided code for bugs, logic errors, and provide a critique.

        Args:
            code (str): The source code to evaluate.
            context (str, optional): Additional context or requirements for the code.

        Returns:
            str: The model's critique.
        """
        system_prompt = (
            "You are an expert Code Critic AI. Your task is to review the provided code "
            "and carefully analyze it for both syntactic/runtime bugs AND logical flaws. "
            "Do not just check if it runs; check if the logic is sound and robust. "
            "Explain any issues clearly, and suggest specific improvements or fixes. "
            "Be comprehensive and precise."
        )

        user_prompt = "Please review the following code:\n\n"
        if context:
            user_prompt += f"Context/Requirements:\n{context}\n\n"
        user_prompt += f"```python\n{code}\n```\n\nProvide your detailed critique covering both bugs and logic:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        with torch.no_grad():
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.3,  # Keep it relatively deterministic for code review
            )

        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[
            0
        ]
        return response


if __name__ == "__main__":
    print(
        "Initializing Critic Model (this may take a while as it downloads the Qwen 3B model weights)..."
    )
    critic = QwenCritic()

    # Sample code with a potential bug (Divide by Zero if empty list) and logic inefficiency
    sample_code = """
def calculate_average(numbers):
    sum = 0
    for num in numbers:
        sum += num
    return sum / len(numbers)
"""

    print("\nCritiquing sample code...")
    result = critic.critique(
        sample_code, context="A function to calculate the average of a list of numbers."
    )
    print("\n--- CRITIQUE RESULT ---")
    print(result)
