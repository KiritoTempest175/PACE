import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread


class LiteracyCriticModel:
    """
    A Literacy Critic model using SmolLM2-1.7B to evaluate text for factual consistency,
    NLI (Natural Language Inference) mapping, and general prose quality.
    """

    def __init__(
        self,
        model_id="HuggingFaceTB/SmolLM2-1.7B-Instruct",
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

        print("Literacy Critic Model loaded successfully.")

    def critique(self, text: str, context: str = "") -> str:
        """
        Evaluate the provided text for logic, flow, and factual mapping against the context.

        Args:
            text (str): The generated text to evaluate.
            context (str, optional): The original prompt or reference material.

        Yields:
            str: Generated critique tokens.
        """
        system_prompt = (
            "You are an expert Editor and Logic Auditor (Critic). Your task is to review the provided text "
            "and carefully analyze it for factual consistency, clarity, and structural flow. "
            "Explain any issues clearly, and suggest specific improvements or rewrites. "
            "Be comprehensive and precise."
        )

        user_prompt = "Please review the following text:\n\n"
        if context:
            user_prompt += f"Context/Original Request:\n{context}\n\n"
        user_prompt += f"Generated Text:\n{text}\n\nProvide your detailed critique:"

        messages = [
            {"role": "user", "content": system_prompt + "\n\n" + user_prompt},
        ]
        # Note: Gemma-2-2b-it chat template expects user/model alternation.
        # Merged system into user prompt for Gemma compatibility.

        prompt_text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        model_inputs = self.tokenizer([prompt_text], return_tensors="pt").to(
            self.device
        )

        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        generation_kwargs = dict(
            **model_inputs,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.3,
            streamer=streamer,
        )

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        for new_text in streamer:
            yield new_text


if __name__ == "__main__":
    print("Initializing Literacy Critic Model...")
    critic = LiteracyCriticModel()

    sample_text = (
        "Microservices are a bad idea because they make everything slower and harder to deploy. "
        "Also, they use a centralized database which causes bottlenecks."
    )

    print("\nCritiquing sample text...")
    result = ""
    for token in critic.critique(
        sample_text, context="Summarize the benefits of microservices architecture."
    ):
        print(token, end="", flush=True)
        result += token
    print("\n--- CRITIQUE RESULT ---")
    print(result)
