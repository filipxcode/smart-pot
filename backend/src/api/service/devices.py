from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from api.models.device import Device
import httpx
from config.settings import get_settings

async def select_device(device_id: int, user_id: UUID, session: AsyncSession) -> Device:
    device = await session.scalar(
        select(Device).where(Device.id == device_id, Device.owner_id == user_id)
    )
    if device is None:
        raise HTTPException(404, "Device not found")
    return device


async def get_primary_device(user_id: UUID, session: AsyncSession) -> Device:
    device = await session.scalar(
        select(Device).where(Device.owner_id == user_id).order_by(Device.id).limit(1)
    )
    if device is None:
        raise HTTPException(404, "No device registered for this user")
    return device

def _arduino_url() -> str:
    url = get_settings().ARDUINO_URL
    if not url:
        raise RuntimeError("ARDUINO_URL is not configured")
    return url


async def water_plant(watering_time: int, device_id: int, user_id: UUID, session: AsyncSession)->bool:
    device = await select_device(device_id, user_id, session)
    async with httpx.AsyncClient(timeout=watering_time + 20) as client:
        response = await client.post(_arduino_url(), params={"api-key":device.serial}, json={"duration_sec": watering_time})
        response.raise_for_status()
    return True