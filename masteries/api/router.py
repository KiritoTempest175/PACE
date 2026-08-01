from masteries.api.schemas import PredictRequest, PredictResponse
from fastapi import APIRouter, UploadFile, File
from masteries.services.chunker import chunk_text
from masteries.services.pdfparser import extracttext, pagenumber
from pathlib import Path
import shutil

router = APIRouter()


@router.get("/")
def root():
    return {"message": "PACE Backend Running"}


@router.get("/health")
def health():
    return {"status": "healthy"}


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    try:
        from masteries.coding.inference.actor_generate import generate_fixes

        fixes = generate_fixes(request.text, num_return_sequences=1)
        return PredictResponse(prediction=fixes[0], status="success")
    except Exception as e:
        return PredictResponse(
            prediction=f"[CPU Fallback] You entered: {request.text}\n\n(Error: {e})",
            status="degraded",
        )


@router.post("/generate")
def generate(request: PredictRequest):
    """
    Primary endpoint: accepts a text prompt from the frontend chat,
    runs it through the Actor→Critic ensemble pipeline, and returns
    the best candidate code. Falls back to a stub echo when GPU
    inference modules are not available (e.g. no CUDA).
    """
    try:
        from masteries.coding.inference.v3_orchestrator import v3_pipeline

        result = v3_pipeline(request.text)
        return {
            "response": result,
            "source": "actor-critic-ensemble",
            "status": "success",
        }
    except Exception as e:
        # Graceful fallback when models are not loaded / no GPU
        return {
            "response": (
                f"[PACE Engine — CPU Fallback]\n\n"
                f"Your prompt was received:\n```\n{request.text}\n```\n\n"
                f"The Actor-Critic ensemble requires a CUDA-capable GPU. "
                f"Running in echo-mode.\n\n"
                f"(Debug: {type(e).__name__}: {e})"
            ),
            "source": "fallback",
            "status": "degraded",
        }


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    # Check if the uploaded file is a PDF
    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Only PDF files are allowed."}

    # Save the file
    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extracttext(str(file_path))
    pages = pagenumber(str(file_path))
    chunks = chunk_text(text)
    return {
        "filename": file.filename,
        "pages": pages,
        "characters": len(text),
        "chunks": len(chunks),
        "preview": chunks[0] if chunks else "",
    }
