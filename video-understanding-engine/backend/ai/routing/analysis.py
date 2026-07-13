import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.auth.jwt import get_current_user
from backend.core.database import get_db
from backend.models.User.user_model import User
from backend.models.Video.video_model import Video
from backend.models.AI.video_analysis import VideoAnalysis
from backend.models.AI.flashcard import Flashcard
from backend.models.AI.quiz_question import QuizQuestion
from backend.models.AI.chapter import Chapter

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


async def _get_owned_video(
    video_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Video:
    """Fetch a video and verify it belongs to the requesting user."""
    result = await db.execute(
        select(Video).where(Video.id == video_id, Video.user_id == current_user.user_id)
    )
    video = result.scalars().first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/summary")
async def get_summary(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the AI-generated summary and key topics for a specific video."""
    await _get_owned_video(video_id, current_user, db)

    result = await db.execute(select(VideoAnalysis).where(VideoAnalysis.video_id == video_id))
    analysis = result.scalars().first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found for this video")

    return {
        "id": analysis.id,
        "video_id": analysis.video_id,
        "summary": analysis.summary,
        "key_topics": analysis.key_topics,
        "created_at": analysis.created_at,
    }


@router.get("/{video_id}/flashcards")
async def get_flashcards(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the AI-generated flashcards for a specific video."""
    await _get_owned_video(video_id, current_user, db)

    result = await db.execute(select(Flashcard).where(Flashcard.video_id == video_id))
    return result.scalars().all()


@router.get("/{video_id}/quiz")
async def get_quiz(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the AI-generated multiple-choice quiz questions for a specific video."""
    await _get_owned_video(video_id, current_user, db)

    result = await db.execute(select(QuizQuestion).where(QuizQuestion.video_id == video_id))
    return result.scalars().all()


@router.get("/{video_id}/chapters")
async def get_chapters(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the AI-generated chapters for a specific video."""
    await _get_owned_video(video_id, current_user, db)

    result = await db.execute(
        select(Chapter).where(Chapter.video_id == video_id).order_by(Chapter.start_time.asc())
    )
    return result.scalars().all()
