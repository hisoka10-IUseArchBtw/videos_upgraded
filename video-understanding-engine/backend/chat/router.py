import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.auth.jwt import get_current_user
from backend.core.database import get_db
from backend.models.User.user_model import User
from backend.models.Video.video_model import Video
from backend.chat.engine import ChatEngine

router = APIRouter(prefix="/chat", tags=["Chat with Video"])

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="The question about the video")

class ChatResponse(BaseModel):
    video_id: str
    question: str
    answer: str

@router.post(
    "/{video_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question about a video",
    description="Uses RAG to find relevant video chunks and generates an answer using an LLM."
)
async def chat_with_video(
    video_id: uuid.UUID,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    # Ownership check
    result = await db.execute(
        select(Video).where(Video.id == video_id, Video.user_id == current_user.user_id)
    )
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Video not found")
    try:
        engine = ChatEngine()
        answer = await engine.generate_chat_response(
            video_id=str(video_id),
            question=body.question
        )
        return ChatResponse(
            video_id=str(video_id),
            question=body.question,
            answer=answer
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat: {str(e)}",
        )
