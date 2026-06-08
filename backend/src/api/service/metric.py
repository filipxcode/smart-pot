from datetime import UTC, datetime, timedelta
from typing import Literal

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.device import Device
from api.models.metric import Metric
from api.schemas.metric import HistorySummary, MetricBucket, MetricIngest


async def ingest_reading(payload: MetricIngest, session: AsyncSession) -> Metric:
    """Persist a sensor reading pushed by the device webhook."""
    device = await session.get(Device, payload.device_id)
    if device is None:
        raise HTTPException(404, "Device not found")
    metric = Metric(**payload.model_dump())
    session.add(metric)
    await session.commit()
    await session.refresh(metric)
    return metric


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

Unit = Literal["hour", "day", "month", "year"]
Granularity = Literal["hour", "day", "week", "month"]

_SENSORS = ("air_temp", "air_hum", "root_temp", "soil_hum", "light_lux")


def _window_start(unit: Unit, amount: int) -> datetime:
    """Builds data period"""
    return datetime.now(UTC) - relativedelta(**{f"{unit}s": amount})


def _auto_granularity(start: datetime) -> Granularity:
    """Window guardial"""
    window = datetime.now(UTC) - start
    if window <= timedelta(days=2):
        return "hour"
    if window <= timedelta(days=60):
        return "day"
    if window <= timedelta(days=180):
        return "week"
    return "month"


def _f(value) -> float | None:
    return round(float(value), 2) if value is not None else None


async def aggregate_history(
    device_id: int,
    session: AsyncSession,
    *,
    unit: Unit = "day",
    amount: int = 1,
) -> HistorySummary:
    """Agregate history according to selected period via type and amount"""
    start = _window_start(unit, amount)
    granularity = _auto_granularity(start)
    bucket = func.date_trunc(granularity, Metric.created_at).label("bucket")
    averages = [func.avg(getattr(Metric, name)).label(name) for name in _SENSORS]

    rows = (
        await session.execute(
            select(bucket, func.count().label("n"), *averages)
            .where(Metric.device_id == device_id, Metric.created_at >= start)
            .group_by(bucket)
            .order_by(bucket.asc())
        )
    ).all()

    buckets = [
        MetricBucket(
            bucket=r._mapping["bucket"],
            count=r._mapping["n"],
            **{name: _f(r._mapping[name]) for name in _SENSORS},
        )
        for r in rows
    ]

    return HistorySummary(
        unit=unit, amount=amount, granularity=granularity, start=start, buckets=buckets
    )
    
    