from pydantic import BaseModel, StrictBool


class DeviceState(BaseModel):
    device_id: str
    enabled: StrictBool
