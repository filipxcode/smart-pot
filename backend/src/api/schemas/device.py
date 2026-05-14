import uuid

from pydantic import BaseModel, ConfigDict


class DeviceCreate(BaseModel):
    name: str
    serial: str


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    serial: str
    owner_id: uuid.UUID

class DeviceUpdate(BaseModel):
    name: str | None = None
    serial: str | None = None