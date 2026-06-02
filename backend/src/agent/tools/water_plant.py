import logging
import httpx
from api.service.devices import water_plant as water_plant_service
from agent.deps import ChatDeps
from pydantic_ai import RunContext

logger = logging.getLogger(__name__)
async def water_plant(ctx: RunContext[ChatDeps], watering_time: int = 10) -> str:
    try:
        await water_plant_service(
            watering_time=watering_time,
            device_id=ctx.deps.device_id,
            user_id=ctx.deps.user_id,
            session=ctx.deps.session,
        )
    except httpx.HTTPError as exc: 
        logger.warning("water_plant failed: %s", exc)
        return f"Nie udało się podlać — urządzenie nie odpowiedziało poprawnie (czas: {watering_time}s)."
    return f"Podlano roślinę przez {watering_time}s."