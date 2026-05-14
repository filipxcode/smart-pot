from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.device import Device
from api.models.device_event import DeviceEvent


async def select_device_event(
    event_id: UUID, user_id: UUID, session: AsyncSession
) -> DeviceEvent:
    event = await session.scalar(
        select(DeviceEvent)
        .join(Device, DeviceEvent.device_id == Device.id)
        .where(DeviceEvent.id == event_id, Device.owner_id == user_id)
    )
    if event is None:
        raise HTTPException(404, "Event not found")
    return event
