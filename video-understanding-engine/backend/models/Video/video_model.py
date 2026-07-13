import uuid
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    
    # Metadata
    duration: Mapped[float] = mapped_column(nullable=True)
    resolution: Mapped[str] = mapped_column(String(50), nullable=True)
    fps: Mapped[float] = mapped_column(nullable=True)
    codec: Mapped[str] = mapped_column(String(50), nullable=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Optional: If you want a back-reference on the user model, you can add it there later.
