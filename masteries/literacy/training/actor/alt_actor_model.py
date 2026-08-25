import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread


class LiteracyActorModel:
    """
    A Literacy Actor model using a ~4B local LLM (e.g., microsoft/Phi-3-mini-4k-instruct)
    to generate and revise text based on user prompts and critiques.
    """

    def __init__(
        self,
        model_id="microsoft/Phi-3-mini-4k-instruct",
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

        print("Literacy Actor Model loaded successfully.")

    def generate_text(self, prompt: str) -> str:
        """
        Understand the user prompt and generate text/summary.

        Args:
            prompt (str): The user requirement or task.

        Yields:
            str: Generated text tokens.
        """
        system_prompt = (
            "You are an expert technical writer and analyst. Your task is to process, summarize, "
            "and clarify text based on the user's requirements. Ensure accuracy and excellent prose."
        )

        user_prompt = (
            f"Please process the following request:\n\n{prompt}\n\nProvide the output:"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

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

    def revise_text(self, prompt: str, original_text: str, critique: str) -> str:
        """
        Understand the critic prompt/critique and revise the text.

        Args:
            prompt (str): The original user requirement.
            original_text (str): The text that had issues.
            critique (str): The feedback from the critic model.

        Yields:
            str: Revised text tokens.
        """
        system_prompt = (
            "You are an expert technical writer. You previously wrote some text that was reviewed "
            "by an Editor (Critic). The critic found areas for improvement. Your task is to "
            "understand the critique and revise the text accordingly. Provide only the revised text."
        )

        user_prompt = (
            f"Original Requirement:\n{prompt}\n\n"
            f"Original Text:\n{original_text}\n\n"
            f"Critic Feedback:\n{critique}\n\n"
            "Please revise the text to address the critic's feedback. Provide the updated text:"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        generation_kwargs = dict(
            **model_inputs,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.5,
            streamer=streamer,
        )

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        for new_text in streamer:
            yield new_text


if __name__ == "__main__":
    print("Initializing Literacy Actor Model...")
    actor = LiteracyActorModel()

    task_prompt = "Summarize the benefits of microservices architecture."

    print("\n--- GENERATING TEXT ---")
    generated = ""
    for token in actor.generate_text(task_prompt):
        print(token, end="", flush=True)
        generated += token
    print()

    print("\n--- REVISING TEXT ---")
    mock_critique = "The text is a bit too technical. Simplify the language for a non-technical audience."
    for token in actor.revise_text(task_prompt, generated, mock_critique):
        print(token, end="", flush=True)
    print()
