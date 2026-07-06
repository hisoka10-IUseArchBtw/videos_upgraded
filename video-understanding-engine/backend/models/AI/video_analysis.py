import uuid
from datetime import datetime
from sqlalchemy import Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.database import Base

class VideoAnalysis(Base):
    __tablename__ = "video_analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    key_topics: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
