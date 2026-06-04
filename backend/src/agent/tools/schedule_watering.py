from datetime import time
from enum import Enum


class Weekday(str, Enum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


async def schedule_watering_plant(
    time_of_day: time,
    days: list[Weekday] | None = None,
    duration_sec: int = 10,
) -> str:
    when = "codziennie" if not days else ", ".join(d.value for d in days)
    return (
        f"Zaplanowano cykliczne podlewanie ({when}) "
        f"o {time_of_day.isoformat(timespec='minutes')} na {duration_sec}s"
    )
