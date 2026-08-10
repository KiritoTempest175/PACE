from pydantic import BaseModel
from typing import Optional


class PredictRequest(BaseModel):
    text: str
    mode: Optional[str] = "coding"
    speed_mode: Optional[str] = "pro"


class PredictResponse(BaseModel):
    prediction: str
    status: str


class TelemetryResponse(BaseModel):
    vram_allocated_mb: float
    vram_total_mb: float
    vram_percent: float
    actor_model: str
    critic_model: str
    tokens_per_sec: float
    latency_ms: int
    device: str
    status: str

