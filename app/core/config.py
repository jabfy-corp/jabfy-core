import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    llm_base_url: str = "http://localhost:8080/v1"
    llm_api_key: str | None = None
    allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    origins = os.getenv("JABFY_ALLOWED_ORIGINS", "http://localhost:5173")
    return Settings(
        host=os.getenv("JABFY_HOST", "0.0.0.0"),
        port=int(os.getenv("JABFY_PORT", "8000")),
        llm_base_url=os.getenv("JABFY_LLM_BASE_URL", "http://localhost:8080/v1"),
        llm_api_key=os.getenv("JABFY_LLM_API_KEY") or None,
        allowed_origins=[
            origin.strip() for origin in origins.split(",") if origin.strip()
        ],
    )
