import uuid
from sqlalchemy import Integer, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from backend.core.database import Base

class VideoChunk(Base):
    __tablename__ = "video_chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(768))
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
