from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from api.models.device import Device

async def select_device(device_id: int, user_id: UUID, session: AsyncSession) -> Device:
    return await session.scalar(
        select(Device).where(Device.id == device_id, Device.owner_id == user_id)
    )