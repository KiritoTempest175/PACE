"""Strict request and response contracts."""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class PredictRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=6000)
    mode: Literal['coding','literacy','research'] = 'coding'
    speed_mode: Literal['fast','pro'] = 'fast'
    document_id: str | None = Field(default=None, max_length=48, pattern=r'^doc-[0-9a-f-]{36}$')
    conversation_id: str | None = Field(default=None, max_length=72, pattern=r'^chat-[0-9a-f-]{32,36}$')

class PredictResponse(BaseModel):
    prediction: str
    status: Literal['success','unavailable']

class CreateConversationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(default='New session', min_length=1, max_length=120)
    workspace: Literal['coding','literacy','research'] = 'coding'

class TelemetryResponse(BaseModel):
    status: str
    device: str
    cpu_utilization: float | None = None
    ram_usage_mb: float | None = None
    gpu_utilization: float | None = None
    vram_allocated_mb: float | None = None
    vram_total_mb: float | None = None
    tokens_per_sec: float | None = None
    latency_ms: int | None = None
    actor_model: str | None = None
    critic_model: str | None = None

class CodeRunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    code: str = Field(min_length=1,max_length=20000)
    test_code: str | None = Field(default=None,max_length=10000)
    timeout: int = Field(default=8,ge=1,le=20)
