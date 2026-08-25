import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread


class ResearchActorModel:
    """
    A Research Actor model using a ~4B local LLM (e.g., microsoft/Phi-3-mini-4k-instruct)
    to synthesize literature, compare architectures, and draft research summaries.
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

        print("Research Actor Model loaded successfully.")

    def generate_research(self, prompt: str) -> str:
        """
        Understand the user prompt and generate academic/research text.

        Args:
            prompt (str): The user requirement or task.

        Yields:
            str: Generated text tokens.
        """
        system_prompt = (
            "You are an expert AI researcher and academic. Your task is to compile literature, "
            "compare architectures, and synthesize findings accurately based on the user's prompt. "
            "Maintain an objective, academic tone."
        )

        user_prompt = f"Please process the following research request:\n\n{prompt}\n\nProvide the synthesis:"

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

    def revise_research(self, prompt: str, original_text: str, critique: str) -> str:
        """
        Understand the critic prompt/critique and revise the research text.

        Args:
            prompt (str): The original user requirement.
            original_text (str): The text that had issues (e.g. missing citations, inaccurate claims).
            critique (str): The feedback from the critic model.

        Yields:
            str: Revised text tokens.
        """
        system_prompt = (
            "You are an expert AI researcher. You previously drafted a synthesis that was reviewed "
            "by a Citation Auditor (Critic). The critic found areas for improvement or inaccuracies. "
            "Your task is to understand the critique and revise the text accordingly. Provide only the revised text."
        )

        user_prompt = (
            f"Original Request:\n{prompt}\n\n"
            f"Original Synthesis:\n{original_text}\n\n"
            f"Critic Feedback:\n{critique}\n\n"
            "Please revise the synthesis to address the critic's feedback. Provide the updated synthesis:"
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
    print("Initializing Research Actor Model...")
    actor = ResearchActorModel()

    task_prompt = "Compare state-space models vs self-attention memory efficiency."

    print("\n--- GENERATING SYNTHESIS ---")
    generated = ""
    for token in actor.generate_research(task_prompt):
        print(token, end="", flush=True)
        generated += token
    print()

    print("\n--- REVISING SYNTHESIS ---")
    mock_critique = "The text lacks mention of KV cache compression. Please add a section on KV cache."
    for token in actor.revise_research(task_prompt, generated, mock_critique):
        print(token, end="", flush=True)
    print()
