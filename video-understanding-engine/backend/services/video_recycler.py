import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.AI.video_analysis import VideoAnalysis
from backend.models.AI.flashcard import Flashcard
from backend.models.AI.quiz_question import QuizQuestion
from backend.models.AI.chapter import Chapter

async def recycle_video(db: AsyncSession, source_video_id: uuid.UUID, new_video_id: uuid.UUID) -> None:
    """
    Copies AI-generated data from a source video to a new video for deduplication.
    """
    # Copy VideoAnalysis
    res_analysis = await db.execute(select(VideoAnalysis).where(VideoAnalysis.video_id == source_video_id))
    source_analysis = res_analysis.scalars().first()
    if source_analysis:
        new_analysis = VideoAnalysis(
            video_id=new_video_id,
            summary=source_analysis.summary,
            key_topics=source_analysis.key_topics,
        )
        db.add(new_analysis)

    # Copy Flashcards
    res_flashcards = await db.execute(select(Flashcard).where(Flashcard.video_id == source_video_id))
    source_flashcards = res_flashcards.scalars().all()
    for fc in source_flashcards:
        new_fc = Flashcard(
            video_id=new_video_id,
            question=fc.question,
            answer=fc.answer,
        )
        db.add(new_fc)

    # Copy QuizQuestions
    res_quiz = await db.execute(select(QuizQuestion).where(QuizQuestion.video_id == source_video_id))
    source_quiz = res_quiz.scalars().all()
    for q in source_quiz:
        new_q = QuizQuestion(
            video_id=new_video_id,
            question=q.question,
            options=q.options,
            correct_answer=q.correct_answer,
        )
        db.add(new_q)

    # Copy Chapters
    res_chapters = await db.execute(select(Chapter).where(Chapter.video_id == source_video_id))
    source_chapters = res_chapters.scalars().all()
    for ch in source_chapters:
        new_ch = Chapter(
            video_id=new_video_id,
            title=ch.title,
            summary=ch.summary,
            start_time=ch.start_time,
            end_time=ch.end_time,
        )
        db.add(new_ch)

    await db.commit()
