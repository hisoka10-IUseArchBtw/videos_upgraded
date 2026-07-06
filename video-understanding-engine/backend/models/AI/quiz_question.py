import uuid
from datetime import datetime
from sqlalchemy import Text, JSON, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.database import Base

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[dict] = mapped_column(JSON)
    correct_answer: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
