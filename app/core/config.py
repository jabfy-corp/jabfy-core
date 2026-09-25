import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    simulation_url: str = "http://127.0.0.1:8080"
    llm_provider: str = "openai_compat"
    llm_base_url: str = "http://localhost:8080/v1"
    llm_api_key: str | None = None
    llm_timeout: float = 120.0
    allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    origins = os.getenv("JABFY_ALLOWED_ORIGINS", "http://localhost:5173")
    # Keep the published simulator Compose compatible without restoring the old SDK.
    legacy_ollama_host = os.getenv("OLLAMA_HOST", "").strip().rstrip("/")
    default_llm_url = (
        f"{legacy_ollama_host}/v1" if legacy_ollama_host else "http://localhost:8080/v1"
    )
    return Settings(
        host=os.getenv("JABFY_HOST", "0.0.0.0"),
        port=int(os.getenv("JABFY_PORT", "8000")),
        simulation_url=os.getenv("JABFY_SIMULATION_URL", "http://127.0.0.1:8080"),
        llm_provider=os.getenv("JABFY_LLM_PROVIDER", "openai_compat"),
        llm_base_url=os.getenv("JABFY_LLM_BASE_URL", default_llm_url),
        llm_api_key=os.getenv("JABFY_LLM_API_KEY") or None,
        llm_timeout=float(os.getenv("JABFY_LLM_TIMEOUT_SECONDS", "120")),
        allowed_origins=[
            origin.strip() for origin in origins.split(",") if origin.strip()
        ],
    )
