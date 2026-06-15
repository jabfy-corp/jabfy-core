import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    ollama_host: str = "http://localhost:11434"
    allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    origins = os.getenv("JABFY_ALLOWED_ORIGINS", "http://localhost:5173")
    return Settings(
        host=os.getenv("JABFY_HOST", "0.0.0.0"),
        port=int(os.getenv("JABFY_PORT", "8000")),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        allowed_origins=[
            origin.strip() for origin in origins.split(",") if origin.strip()
        ],
    )
