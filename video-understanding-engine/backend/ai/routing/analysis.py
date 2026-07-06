import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.database import get_db
from backend.models.AI.video_analysis import VideoAnalysis
from backend.models.AI.flashcard import Flashcard
from backend.models.AI.quiz_question import QuizQuestion

router = APIRouter(prefix="/ai", tags=["AI Analysis"])

@router.get("/{video_id}/summary")
async def get_summary(video_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Retrieve the AI-generated summary and key topics for a specific video.
    """
    result = await db.execute(select(VideoAnalysis).where(VideoAnalysis.video_id == video_id))
    analysis = result.scalars().first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found for this video")
        
    return {
        "id": analysis.id,
        "video_id": analysis.video_id,
        "summary": analysis.summary,
        "key_topics": analysis.key_topics,
        "created_at": analysis.created_at
    }

@router.get("/{video_id}/flashcards")
async def get_flashcards(video_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Retrieve the AI-generated flashcards for a specific video.
    """
    result = await db.execute(select(Flashcard).where(Flashcard.video_id == video_id))
    flashcards = result.scalars().all()
    
    return flashcards

@router.get("/{video_id}/quiz")
async def get_quiz(video_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Retrieve the AI-generated multiple-choice quiz questions for a specific video.
    """
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.video_id == video_id))
    questions = result.scalars().all()
    
    return questions
