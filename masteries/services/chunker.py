def chunk_text(text: str, chunk_size: int = 1000):
    chunks = []

    for i in range(0, len(text), chunk_size):
        chunks.append(text[i : i + chunk_size])

    return chunks


if __name__ == "__main__":
    text = "Hello " * 500
    chunks = chunk_text(text)
    print(len(chunks))
