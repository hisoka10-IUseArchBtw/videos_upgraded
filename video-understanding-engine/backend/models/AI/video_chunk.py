import uuid
from typing import Optional
from sqlalchemy import Integer, Text, Float, ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.database import Base


class VideoChunk(Base):
    __tablename__ = "video_chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    chunk_type: Mapped[str] = mapped_column(
        String(32), default="transcript", index=True
    )  # "transcript" | "ocr" | "chapter" | "summary"
    start_time: Mapped[float] = mapped_column(Float, default=0.0)
    end_time: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSON, nullable=True
    )  # speaker label, chapter title, etc.
