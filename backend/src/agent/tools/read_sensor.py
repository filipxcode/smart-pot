from pydantic_ai import RunContext

from agent.deps import ChatDeps
from api.models.metric import SENSOR_LABELS, Sensor
from api.service.metric import get_latest


def _format(readings: dict[str, float | None]) -> str:
    parts = []
    for key, value in readings.items():
        label = SENSOR_LABELS[Sensor(key)]
        parts.append(f"{label}: {value}" if value is not None else f"{label}: brak odczytu")
    return "; ".join(parts)


async def read_sensor(ctx: RunContext[ChatDeps]) -> str:
    """Reading health params"""
    metric = await get_latest(ctx.deps.device_id, ctx.deps.session)
    if metric is None:
        return "Brak zapisanych odczytów z czujników dla tego urządzenia."
    readings = {sensor.value: getattr(metric, sensor.value) for sensor in Sensor}
    return _format(readings)
