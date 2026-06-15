from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class ActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    prompt: str
    device_state: dict[str, StrictBool] = Field(default_factory=dict)


class UserSituationPayload(BaseModel):
    prompt: str
    device_state: dict[str, StrictBool] = Field(default_factory=dict)


class UniversalBusEvent(BaseModel):
    source: str
    event_type: Literal["user_situation"]
    payload: UserSituationPayload


class ActionProposal(BaseModel):
    action_chain: str
    changes: dict[str, Any] = Field(default_factory=dict)


class VerificationDecision(BaseModel):
    allowed: bool
    reason: str
    safe_changes: dict[str, bool] = Field(default_factory=dict)


class ActionResponse(BaseModel):
    action_chain: str
    changes: dict[str, bool] = Field(default_factory=dict)
    verification: VerificationDecision
