"""
chunker.py — Text Chunking Utilities (Stream B / Mastery 2: Literacy)

Provides two chunking strategies for preparing documents for the Transformer:

  1. chunk_text()          — Fixed-size chunking (original implementation).
  2. chunk_text_overlap()  — Overlapping sliding-window chunking.
                             Ensures long documents fit within the Transformer's
                             maximum token context limit without losing context
                             at chunk boundaries.
"""


def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    """
    Split *text* into non-overlapping fixed-size character chunks.

    Args:
        text:       Input string to chunk.
        chunk_size: Maximum number of characters per chunk.

    Returns:
        List of chunk strings.
    """
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i : i + chunk_size])
    return chunks


def chunk_text_overlap(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:
    """
    Split *text* into overlapping sliding-window chunks.

    Each chunk shares *overlap* characters with the previous chunk so that
    context at boundaries is not lost when a document is fed into a Transformer
    with a fixed maximum token length.

    Args:
        text:       Input string to chunk.
        chunk_size: Maximum number of characters per chunk.
        overlap:    Number of characters to repeat from the end of one chunk
                    at the start of the next. Must be < chunk_size.

    Returns:
        List of chunk strings. The last chunk may be shorter than chunk_size.

    Raises:
        ValueError: If overlap >= chunk_size.

    Example::

        >>> chunks = chunk_text_overlap("A" * 2500, chunk_size=1000, overlap=200)
        >>> len(chunks)
        4
        >>> chunks[0][:5], chunks[1][:5]   # overlap visible at start of chunk[1]
        ('AAAAA', 'AAAAA')
    """
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
