import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from api.base import Base


class EventType(Enum):
    WATERING = "watering" 
    FERTILIZATION = "fertilization" # Nawoz
    REPOTTING = "repotting" # Przesadzanie
    LOCATION_CHANGE = "location_change" 
    PRUNING = "pruning" #Przyciecie
    PEST_TREATMENT = "pest_treatment" #Leczenie/opryski na pasozyty 


class DeviceEvent(Base):
    __tablename__ = "device_event"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    event_type: Mapped[EventType]
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
