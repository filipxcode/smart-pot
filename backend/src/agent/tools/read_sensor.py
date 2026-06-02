from api.models.metric import SENSOR_LABELS, Sensor
from api.service.devices import read_sensor as read_sensor_service
from agent.deps import ChatDeps
from pydantic_ai import RunContext

def _format(readings: dict[str, float | None]) -> str:
    parts = []
    for key, value in readings.items():
        label = SENSOR_LABELS[Sensor(key)]
        parts.append(f"{label}: {value}" if value is not None else f"{label}: brak odczytu")
    return "; ".join(parts)

async def read_sensor(ctx: RunContext[ChatDeps], sensors: list[Sensor]) -> str:
    readings = await read_sensor_service(
        sensors=sensors,
        device_id=ctx.deps.device_id,
        user_id=ctx.deps.user_id,
        session=ctx.deps.session,
    )
    return _format(readings)