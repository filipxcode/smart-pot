from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from api.models.device import Device
from api.models.metric import Sensor, SENSOR_LABELS
import httpx
from config.settings import get_settings

async def select_device(device_id: int, user_id: UUID, session: AsyncSession) -> Device:
    device = await session.scalar(
        select(Device).where(Device.id == device_id, Device.owner_id == user_id)
    )
    if device is None:
        raise HTTPException(404, "Device not found")
    return device

async def read_sensor(sensors: list[Sensor], device_id: int, user_id: UUID, session: AsyncSession)->list[str]:
    device = await select_device(device_id, user_id, session)
    async with httpx.AsyncClient() as client:
        response = await client.get(get_settings().ARDUINO_URL, params={"api-key":device.serial})
        response.raise_for_status()
    data = response.json()
    return {s.value: data.get(s.value) for s in sensors} 


async def water_plant(watering_time: int, device_id: int, user_id: UUID, session: AsyncSession)->bool:
    device = await select_device(device_id, user_id, session)
    async with httpx.AsyncClient(timeout=watering_time + 20) as client:
        response = await client.post(get_settings().ARDUINO_URL, params={"api-key":device.serial}, json={"duration_sec": watering_time})
        response.raise_for_status()
    return True