from pydantic import BaseModel
import uuid
from datetime import datetime

class VideoResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
