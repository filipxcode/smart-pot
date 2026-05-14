from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import current_active_user
from api.db import get_async_session
from api.models.device import Device
from api.models.device_event import DeviceEvent
from api.models.user import User
from api.schemas.device_event import (
    DeviceEventCreate,
    DeviceEventRead,
    DeviceEventUpdate,
)
from api.service.device_event import select_device_event
from api.service.devices import select_device

router = APIRouter(prefix="/device-events", tags=["device-events"])


@router.get("", response_model=list[DeviceEventRead])
async def list_my_device_events(
    device_id: int | None = None,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(DeviceEvent)
        .join(Device, DeviceEvent.device_id == Device.id)
        .where(Device.owner_id == user.id)
        .order_by(DeviceEvent.created_at.desc())
    )
    if device_id is not None:
        stmt = stmt.where(DeviceEvent.device_id == device_id)
    result = await session.scalars(stmt)
    return result.all()


@router.get("/{event_id}", response_model=DeviceEventRead)
async def get_device_event(
    event_id: UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await select_device_event(event_id, user.id, session)


@router.post("", response_model=DeviceEventRead, status_code=status.HTTP_201_CREATED)
async def create_device_event(
    payload: DeviceEventCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    await select_device(payload.device_id, user.id, session)

    event = DeviceEvent(**payload.model_dump())
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


@router.patch("/{event_id}", response_model=DeviceEventRead)
async def update_device_event(
    event_id: UUID,
    payload: DeviceEventUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    event = await select_device_event(event_id, user.id, session)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    await session.commit()
    await session.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_event(
    event_id: UUID,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    event = await select_device_event(event_id, user.id, session)
    await session.delete(event)
    await session.commit()
