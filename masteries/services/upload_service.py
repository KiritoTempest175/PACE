"""PDF-only ingestion with UUID paths, transport caps, and bounded extraction."""
from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

import fitz
from fastapi import UploadFile

from core.config import Settings


class UploadFailure(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _extract_pdf(target: Path, settings: Settings) -> dict:
    """Run blocking MuPDF work on the thread pool, not FastAPI's event loop."""
    try:
        with fitz.open(target, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise UploadFailure("Password-protected PDFs are not supported")
            pages = len(pdf)
            if pages > settings.max_pdf_pages:
                raise UploadFailure("PDF exceeds page limit", 413)
            chunks: list[str] = []
            total = 0
            for page in pdf:
                text = page.get_text("text")
                total += len(text)
                if total > settings.max_pdf_text_chars:
                    raise UploadFailure("PDF exceeds extracted-text limit", 413)
                if text.strip():
                    chunks.append(text.strip())
    except UploadFailure:
        raise
    except (fitz.FileDataError, RuntimeError, ValueError) as exc:
        raise UploadFailure("Could not parse PDF") from exc
    if not chunks:
        raise UploadFailure("PDF contains no extractable text")
    full_text = "\n".join(chunks)
    return {
        "extracted_text": full_text,
        "filename": "document.pdf",
        "pages": pages,
        "characters": total,
        "chunks": len(chunks),
        "preview": full_text[:1200],
        "status": "success",
        "message": "PDF processed; the uploaded binary was deleted",
    }


async def process_pdf(file: UploadFile, settings: Settings) -> dict:
    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise UploadFailure("Only PDF uploads are accepted")
    root = Path(settings.upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / f"{uuid4().hex}.pdf").resolve()
    if root not in target.parents:
        raise UploadFailure("Invalid upload destination")
    written = 0
    try:
        with target.open("xb") as output:
            first = await file.read(5)
            if first != b"%PDF-":
                raise UploadFailure("File does not contain a PDF signature")
            output.write(first)
            written += len(first)
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > settings.max_upload_bytes:
                    raise UploadFailure("PDF exceeds upload limit", 413)
                output.write(chunk)
        return await asyncio.to_thread(_extract_pdf, target, settings)
    finally:
        await file.close()
        target.unlink(missing_ok=True)
