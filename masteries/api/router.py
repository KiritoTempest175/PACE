from masteries.api.schemas import PredictRequest, PredictResponse
from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import shutil

router = APIRouter()

@router.get("/")
def root():
    return {
        "message": "PACE Backend Running 🚀"
    }

@router.get("/health")
def health():
    return {
        "status": "healthy"
    }

@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    return PredictResponse(
        prediction=f"You entered: {request.text}",
        status="success"
    )


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    # Check if the uploaded file is a PDF
    if not file.filename.lower().endswith(".pdf"):
        return {
            "error": "Only PDF files are allowed."
        }

    # Save the file
    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "message": "File uploaded successfully"
    }


# Later, you'll simply replace the dummy logic with a call to Stream A's AI model:
# prediction = actor_model.generate(request.text)