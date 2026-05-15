import uuid
from sqlalchemy import ForeignKey, Float, Integer, DateTime                                                                                                                                                 
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from api.base import Base
from datetime import datetime

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