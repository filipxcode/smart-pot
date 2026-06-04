from typing import Annotated

from pydantic import Field
from pydantic_ai import RunContext

from agent.deps import ChatDeps
from api.models.metric import SENSOR_LABELS, Sensor
from api.schemas.metric import HistorySummary
from api.service.metric import Unit, aggregate_history


def _format(summary: HistorySummary) -> str:
    if not summary.buckets:
        return "Brak danych historycznych w tym zakresie."

    lines = [
        f"Historia ({summary.amount} {summary.unit}, kubełki: {summary.granularity}):"
    ]
    for b in summary.buckets:
        ts = b.bucket.strftime("%Y-%m-%d %H:%M")
        parts = [
            f"{SENSOR_LABELS[sensor]} śr {getattr(b, sensor.value)}"
            for sensor in Sensor
            if getattr(b, sensor.value) is not None
        ]
        lines.append(f"{ts} — " + "; ".join(parts) if parts else f"{ts} — brak odczytów")
    return "\n".join(lines)


async def read_historical_data(
    ctx: RunContext[ChatDeps],
    unit: Unit = "day",
    amount: Annotated[int, Field(ge=1, le=365)] = 7,
) -> str:
    """Zwraca zagregowaną historię parametrów (avg/min/max per sensor) w kubełkach
    czasowych. unit = jednostka zakresu (hour/day/month/year), amount = ile jednostek
    wstecz (np. unit='hour', amount=24 → ostatnie 24h)."""
    summary = await aggregate_history(
        ctx.deps.device_id, ctx.deps.session, unit=unit, amount=amount
    )
    return _format(summary)
