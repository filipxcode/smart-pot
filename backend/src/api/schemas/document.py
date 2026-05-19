from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class DocumentRead(BaseModel):
    id: int
    title: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class DocumentRawRead(BaseModel):
    id: int
    title: str
    raw_text: str
    model_config = ConfigDict(from_attributes=True)


class ChunkRead(BaseModel):
    id: int
    text: str
    model_config = ConfigDict(from_attributes=True)

