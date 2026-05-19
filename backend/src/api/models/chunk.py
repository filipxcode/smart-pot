from api.base import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Chunk(Base):
    __tablename__ = "chunks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    text: Mapped[str]
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    
    
    document: Mapped["DocumentModel"] = relationship(back_populates="chunks")