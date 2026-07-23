from fastapi import APIRouter

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
@router.post("/predict")
def predict():
    return {
        "prediction": "Dummy Prediction",
        "status": "success"
    }