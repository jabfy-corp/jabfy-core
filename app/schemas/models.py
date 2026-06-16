from pydantic import BaseModel, Field


class ModelsResponse(BaseModel):
    models: list[str] = Field(default_factory=list)
    available: bool
    reason: str | None = None
