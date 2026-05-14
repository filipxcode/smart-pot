from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import current_active_user
from api.db import get_async_session
from api.models.metric import Metric
from api.models.user import User
from api.schemas.metric import MetricCreate, MetricRead
from api.service.devices import select_device
from api.service.metric import get_latest, list_history

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/{device_id}/history", response_model=list[MetricRead])
async def get_history( device_id: int,days: int = Query(7, ge=1, le=365), user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    await select_device(device_id, user.id, session)
    return await list_history(device_id, days, session)


@router.get("/{device_id}/latest", response_model=MetricRead | None)
async def get_latest_metric(device_id: int, user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    await select_device(device_id, user.id, session)
    return await get_latest(device_id, session)


@router.post("", response_model=MetricRead, status_code=status.HTTP_201_CREATED)
async def create_metric(payload: MetricCreate, user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    await select_device(payload.device_id, user.id, session)
    metric = Metric(**payload.model_dump())
    session.add(metric)
    await session.commit()
    await session.refresh(metric)
    return metric
