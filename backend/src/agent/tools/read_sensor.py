import logging

import httpx
from pydantic_ai import RunContext

from agent.deps import ChatDeps
from api.models.metric import SENSOR_LABELS, Sensor
from api.service.devices import read_sensor as read_sensor_service

logger = logging.getLogger(__name__)


def _format(readings: dict[str, float | None]) -> str:
    parts = []
    for key, value in readings.items():
        label = SENSOR_LABELS[Sensor(key)]
        parts.append(f"{label}: {value}" if value is not None else f"{label}: brak odczytu")
    return "; ".join(parts)

async def read_sensor(ctx: RunContext[ChatDeps]) -> str:
    """Reading health params"""
    try:
        readings = await read_sensor_service(
            device_id=ctx.deps.device_id,
            user_id=ctx.deps.user_id,
            session=ctx.deps.session,
        )
    except (httpx.HTTPError, RuntimeError) as exc:
        logger.warning("read_sensor failed: %s", exc)
        return "Nie udało się odczytać czujników — urządzenie jest teraz niedostępne."
    return _format(readings)