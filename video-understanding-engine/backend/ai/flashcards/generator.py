import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.AI.flashcard import Flashcard
from backend.ai.prompts import FLASHCARD_PROMPT
from backend.ai.providers.gemini import GeminiProvider

async def generate_and_store_flashcards(db: AsyncSession, video_id: uuid.UUID, transcript: str):
    provider = GeminiProvider()
    
    # Generate flashcards JSON array
    results = await provider.generate_json(FLASHCARD_PROMPT, transcript=transcript)
    
    if not isinstance(results, list):
        results = [results] # fallback if the LLM returns a single object instead of list
        
    flashcards = []
    for item in results:
        fc = Flashcard(
            video_id=video_id,
            question=item.get("question", ""),
            answer=item.get("answer", "")
        )
        db.add(fc)
        flashcards.append(fc)
        
    return flashcards
