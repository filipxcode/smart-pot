from datetime import datetime
import uuid

from api.base import Base
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class DocumentModel(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    raw_text: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",  
        passive_deletes=True,          
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    status: Mapped[str] = mapped_column(default="processing")