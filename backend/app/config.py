from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    database_url: str = ""
    ai_daily_budget_usd: float = Field(default=0.25, ge=0, le=100)
    ai_input_usd_per_million: float = Field(default=0.40, ge=0)
    ai_output_usd_per_million: float = Field(default=1.60, ge=0)
    content_buffer_low: int = Field(default=20, ge=1, le=500)
    content_buffer_target: int = Field(default=100, ge=1, le=1000)
    ai_batch_size: int = Field(default=6, ge=1, le=12)
    frontend_origin: str = "http://localhost:3000"
    learning_timezone: str = "America/Monterrey"


config = Config()
