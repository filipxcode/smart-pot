from api.models.metric import SENSOR_LABELS, Sensor


async def read_sensor(sensors: list[Sensor]) -> str:
    # stub: read real sensor values for the given Metric columns
    readings = [f"{SENSOR_LABELS[s]}: 25 stopni" for s in sensors]
    return "; ".join(readings)
