import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.auth import current_active_user
from api.db import get_async_session
from api.models.device import Device
from api.models.metric import Sensor
from api.models.user import User
from api.service.devices import select_device, water_plant, read_sensor
from api.schemas.device import DeviceCreate, DeviceRead, DeviceUpdate

router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("")
async def list_my_devices(user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    result = await session.scalars(
        select(Device).where(Device.owner_id == user.id)
    )
    return result.all()

@router.get("/{device_id}")
async def get_device(device_id: int, user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    return await select_device(device_id, user.id, session)

@router.post("", response_model=DeviceRead)
async def create_device(device: DeviceCreate, user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    device = Device(**device.model_dump(), owner_id=user.id)
    session.add(device)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Device with this serial already exists")
    await session.refresh(device)
    return device

@router.patch("/{device_id}", response_model=DeviceRead)
async def update_device(device_id: int, payload: DeviceUpdate, user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session),):
    device = await select_device(device_id, user.id, session)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    await session.commit()
    await session.refresh(device)
    return device

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    device = await select_device(device_id, user.id, session)
    await session.delete(device)
    await session.commit()
    
@router.post("/{device_id}/water")
async def create_water_event(
    device_id: int,
    watering_time: int = Query(10, ge=1, le=120),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        await water_plant(watering_time, device_id, user.id, session)
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Urządzenie nie odpowiada") from exc
    return {"status": "ok", "watering_time": watering_time}

@router.get("/{device_id}/read-sensor")
async def read_sensor_event(
    device_id: int,
    sensors: list[Sensor] | None = Query(None),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    selected = sensors or list(Sensor)
    try:
        return await read_sensor(selected, device_id, user.id, session)
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Urządzenie nie odpowiada") from exc