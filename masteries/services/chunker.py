
def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i : i + chunk_size])
    return chunks


def chunk_text_overlap(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:

    if overlap >= chunk_size:
        raise ValueError(
            f"overlap ({overlap}) must be less than chunk_size ({chunk_size})."
        )
    if not text:
        return []

    step = chunk_size - overlap
    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += step

    return chunks


if __name__ == "__main__":
    sample = "Hello " * 500

    fixed = chunk_text(sample)
    print(f"Fixed chunks   : {len(fixed)}")

    overlapping = chunk_text_overlap(sample, chunk_size=1000, overlap=200)
    print(f"Overlap chunks : {len(overlapping)}")

    # Verify overlap: last 200 chars of chunk[0] == first 200 chars of chunk[1]
    if len(overlapping) > 1:
        assert overlapping[0][-200:] == overlapping[1][:200], "Overlap mismatch!"
        print("Overlap verified OK")
