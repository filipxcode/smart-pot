import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from api.models.device_event import EventType


class DeviceEventCreate(BaseModel):
    device_id: int
    event_type: EventType
    note: str | None = None


class DeviceEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    device_id: int
    event_type: EventType
    note: str | None
    created_at: datetime


class DeviceEventUpdate(BaseModel):
    note: str | None = None
