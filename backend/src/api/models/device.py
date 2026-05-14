import uuid
from sqlalchemy import ForeignKey                                                                                                                                                
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.base import Base
from api.models.user import User

class Device(Base):
    __tablename__ = "device"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    owner: Mapped[User] = relationship(back_populates="devices")
    