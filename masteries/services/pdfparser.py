import fitz


def extracttext(pdf_path: str) -> str:
    document = fitz.open(pdf_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


def pagenumber(pdf_path: str) -> int:
    document = fitz.open(pdf_path)

    pages = len(document)

    document.close()

    return pages
