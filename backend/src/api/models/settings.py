from datetime import datetime
from sqlalchemy import Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from api.base import Base

class DeviceSettings(Base):
    __tablename__ = "device_settings"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), unique=True, index=True)
    auto_water_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    moisture_threshold: Mapped[int] = mapped_column(Integer, default=20)
    pump_duration_sec: Mapped[int] = mapped_column(Integer, default=5)
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )