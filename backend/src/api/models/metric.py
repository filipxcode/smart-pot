import uuid
from enum import Enum
from sqlalchemy import ForeignKey, Float, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from api.base import Base
from datetime import datetime


class Sensor(str, Enum):
    AIR_TEMP = "air_temp"
    AIR_HUM = "air_hum"
    ROOT_TEMP = "root_temp"
    SOIL_HUM = "soil_hum"
    LIGHT_LUX = "light_lux"


SENSOR_LABELS: dict[Sensor, str] = {
    Sensor.AIR_TEMP: "temperatura powietrza",
    Sensor.AIR_HUM: "wilgotność powietrza",
    Sensor.ROOT_TEMP: "temperatura korzeni",
    Sensor.SOIL_HUM: "wilgotność gleby",
    Sensor.LIGHT_LUX: "natężenie światła",
}


class Metric(Base):
    __tablename__ = "metric"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"), index=True)
    air_temp: Mapped[float | None] = mapped_column(Float, nullable=True) # temp powietrza
    air_hum: Mapped[float | None] = mapped_column(Float, nullable=True) # wilgotnosc powietrza
    root_temp: Mapped[float | None] = mapped_column(Float, nullable=True) # temp korzeni
    soil_hum: Mapped[int | None] = mapped_column(Integer, nullable=True) # wilgotnosc gleby
    light_lux: Mapped[float | None] = mapped_column(Float, nullable=True) # natezenie swiatla
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        index=True
    )