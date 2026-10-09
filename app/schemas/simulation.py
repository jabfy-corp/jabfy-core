"""Dynamic simulation inventory and proposal-only API contracts."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator


class InventoryModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="allow")


class SimulationRoom(InventoryModel):
    id: str = Field(min_length=1)
    name: str


class SimulationHome(InventoryModel):
    id: str = Field(min_length=1)
    name: str
    rooms: list[SimulationRoom]


class SimulationCapability(InventoryModel):
    action: str = Field(min_length=1)
    label: str
    params: dict[str, Any]


class SimulationDevice(InventoryModel):
    id: str = Field(min_length=1)
    name: str
    type: str
    room_id: str
    room_name: str
    state: dict[str, Any]
    actions: list[SimulationCapability]
    sensor_events: list[Any] = Field(default_factory=list)


class SimulationContext(InventoryModel):
    schema_version: StrictInt
    home: SimulationHome
    revision: str = Field(min_length=1)
    simulation: StrictBool
    status: str
    devices: list[SimulationDevice]

    @field_validator("schema_version")
    @classmethod
    def supported_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError("Unsupported simulation context schema version")
        return value

    @field_validator("simulation")
    @classmethod
    def simulation_only(cls, value: bool) -> bool:
        if not value:
            raise ValueError("The inventory must describe a simulation")
        return value

    @model_validator(mode="after")
    def unambiguous_inventory(self) -> "SimulationContext":
        room_ids = [room.id for room in self.home.rooms]
        device_ids = [device.id for device in self.devices]
        if len(room_ids) != len(set(room_ids)) or len(device_ids) != len(set(device_ids)):
            raise ValueError("Duplicate room or device IDs in simulation inventory")
        for device in self.devices:
            if device.room_id not in room_ids:
                raise ValueError("Device references an unknown room")
            actions = [capability.action for capability in device.actions]
            if len(actions) != len(set(actions)):
                raise ValueError("Duplicate device actions in simulation inventory")
        return self


class ProposalRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)


class SimulationCommand(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    device_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    params: dict[str, Any]


class ModelProposal(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    explanation: str = Field(min_length=1)
    commands: list[SimulationCommand]


class SimulationProposal(ModelProposal):
    context_revision: str
