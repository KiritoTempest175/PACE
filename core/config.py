from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(
    BaseSettings
):  # Renamed to 'Settings' following PEP 8 PascalCase conventions
    gpu_device: str = Field("cuda:0")
    max_vram_mb: int = Field(7500)
    api_host: str = Field("0.0.0.0")
    api_port: int = Field(8000)
    models_dir: str = Field("./masteries")
    max_sequence_length: int = Field(2048)
    max_critic_iterations: int = Field(5)
    log_level: str = Field("INFO")

    # Tells Pydantic to read overrides from your .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> Settings:

    return Settings()
