from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class GenerationParams(BaseModel):
    """Sampling parameters forwarded to llama.cpp.

    Every field is optional. An unset field is omitted from the request so the
    llama.cpp server keeps its own default.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    top_k: int | None = Field(default=None, ge=0)
    min_p: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        validation_alias=AliasChoices("max_tokens", "n_predict"),
    )
    seed: int | None = Field(default=None)
    stop: list[str] | None = Field(default=None)

    def to_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)
