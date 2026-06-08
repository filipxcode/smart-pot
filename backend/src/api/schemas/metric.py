from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MetricCreate(BaseModel):
    device_id: int
    air_temp: float | None = None
    air_hum: float | None = None
    root_temp: float | None = None
    soil_hum: int | None = None
    light_lux: float | None = None


class MetricIngest(BaseModel):
    """Payload pushed by the ESP webhook (device identified by device_id)."""

    device_id: int
    air_temp: float | None = None
    air_hum: float | None = None
    root_temp: float | None = None
    soil_hum: int | None = None
    light_lux: float | None = None


class MetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    air_temp: float | None
    air_hum: float | None
    root_temp: float | None
    soil_hum: int | None
    light_lux: float | None
    created_at: datetime


class MetricBucket(BaseModel):
    bucket: datetime
    count: int
    air_temp: float | None = None
    air_hum: float | None = None
    root_temp: float | None = None
    soil_hum: float | None = None
    light_lux: float | None = None


class HistorySummary(BaseModel):
    unit: str
    amount: int
    granularity: str
    start: datetime
    buckets: list[MetricBucket]
