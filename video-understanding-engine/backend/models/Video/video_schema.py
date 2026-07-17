from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional

class VideoResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class VideoWithThumbnail(VideoResponse):
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None
