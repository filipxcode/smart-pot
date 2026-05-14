from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.metric import Metric


async def list_history(device_id: int, days: int, session: AsyncSession) -> list[Metric]:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    result = await session.scalars(
        select(Metric)
        .where(Metric.device_id == device_id, Metric.created_at >= cutoff)
        .order_by(Metric.created_at.asc())
    )
    return list(result.all())


async def get_latest(device_id: int, session: AsyncSession) -> Metric | None:
    return await session.scalar(
        select(Metric)
        .where(Metric.device_id == device_id)
        .order_by(Metric.created_at.desc())
        .limit(1)
    )
