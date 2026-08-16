from pydantic import BaseModel
from typing import Optional, List, Any


class PredictRequest(BaseModel):
    text: str
    mode: Optional[str] = "coding"
    speed_mode: Optional[str] = "pro"
    conversation_id: Optional[str] = None


class PredictResponse(BaseModel):
    prediction: str
    status: str


class TelemetryResponse(BaseModel):
    vram_allocated_mb: Optional[float] = None
    vram_total_mb: Optional[float] = None
    vram_percent: Optional[float] = None
    gpu_utilization: Optional[float] = None
    cpu_utilization: Optional[float] = None
    ram_usage_mb: Optional[float] = None
    actor_model: str
    critic_model: str
    tokens_per_sec: Optional[float] = None
    latency_ms: Optional[int] = None
    ttft_ms: Optional[int] = None
    generation_time_s: Optional[float] = None
    tokens_generated: Optional[int] = None
    device: str
    status: str
    timestamp: Optional[float] = None


class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Session"
    workspace: Optional[str] = "coding"


class MessageSchema(BaseModel):
    id: str
    role: str
    text: str
    source: Optional[str] = None
    status: Optional[str] = None
    created_at: str


class ConversationSchema(BaseModel):
    id: str
    title: str
    workspace: str
    created_at: str
    updated_at: str
    messages: Optional[List[MessageSchema]] = None
