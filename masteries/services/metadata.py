def metadata(filename, pages, text, chunks):
    return {
        "filename": filename,
        "pages": pages,
        "characters": len(text),
        "chunks": [
            {
                "id": index + 1,
                "length": len(chunk),
                "text": chunk
            }
            for index, chunk in enumerate(chunks)
        ]
    }