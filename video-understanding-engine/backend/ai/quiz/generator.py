import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.AI.quiz_question import QuizQuestion
from backend.ai.prompts import QUIZ_PROMPT
from backend.ai.providers import get_provider, ensure_list

async def generate_and_store_quiz(db: AsyncSession, video_id: uuid.UUID, transcript: str):
    provider = get_provider()
    
    # Generate quiz JSON array
    results_raw = await provider.generate_json(QUIZ_PROMPT, transcript=transcript)
    results = ensure_list(results_raw)
        
    questions = []
    for item in results:
        q = QuizQuestion(
            video_id=video_id,
            question=item.get("question", ""),
            options=item.get("options", []),
            correct_answer=item.get("correct_answer", "")
        )
        db.add(q)
        questions.append(q)
        
    return questions
