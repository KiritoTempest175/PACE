"""Validated configuration shared by the API and its services."""
from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    environment: Literal['development', 'production', 'test'] = 'development'
    database_url: str = 'sqlite:///./backend/pace.db'
    cors_origins: str = 'https://pace-ensemble.netlify.app'
    max_upload_bytes: int = Field(default=8 * 1024 * 1024, ge=1024, le=50 * 1024 * 1024)
    max_pdf_pages: int = Field(default=80, ge=1, le=300)
    max_pdf_text_chars: int = Field(default=100_000, ge=1000, le=500_000)
    upload_dir: str = './uploads'
    rate_limit_per_minute: int = Field(default=30, ge=1, le=1000)
    ai_provider: Literal['local', 'ollama', 'huggingface', 'disabled'] = 'disabled'
    ollama_base_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = 'qwen2.5-coder:1.5b'
    hf_space_id: str = ''
    hf_token: str = ''
    ai_timeout_seconds: int = Field(default=90, ge=5, le=300)
    max_new_tokens: int = Field(default=256, ge=16, le=1024)
    sandbox_enabled: bool = False
    sandbox_image: str = 'pace-sandbox:local'
    tokenizer_backend: Literal['python', 'rust'] = 'python'
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'INFO'

    @property
    def allowed_origins(self) -> list[str]:
        return [v.strip().rstrip('/') for v in self.cors_origins.split(',') if v.strip()]

    @field_validator('cors_origins')
    @classmethod
    def check_origins(cls, value: str) -> str:
        if '*' in value:
            raise ValueError('Wildcard CORS origins are prohibited')
        return value

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
