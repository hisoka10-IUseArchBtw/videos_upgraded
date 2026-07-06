import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.AI.quiz_question import QuizQuestion
from backend.ai.prompts import QUIZ_PROMPT
from backend.ai.providers.gemini import GeminiProvider

async def generate_and_store_quiz(db: AsyncSession, video_id: uuid.UUID, transcript: str):
    provider = GeminiProvider()
    
    # Generate quiz JSON array
    results = await provider.generate_json(QUIZ_PROMPT, transcript=transcript)
    
    if not isinstance(results, list):
        results = [results] # fallback
        
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
