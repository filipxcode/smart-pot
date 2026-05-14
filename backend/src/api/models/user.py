from fastapi_users.db import SQLAlchemyBaseUserTableUUID                                                                                                                                           
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.base import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    devices: Mapped[list["Device"]] = relationship(back_populates="owner")