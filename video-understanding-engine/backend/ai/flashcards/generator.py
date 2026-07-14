import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.AI.flashcard import Flashcard
from backend.ai.prompts import FLASHCARD_PROMPT
from backend.ai.providers import get_provider, ensure_list

async def generate_and_store_flashcards(db: AsyncSession, video_id: uuid.UUID, transcript: str):
    provider = get_provider()
    
    # Generate flashcards JSON array
    results_raw = await provider.generate_json(FLASHCARD_PROMPT, transcript=transcript)
    results = ensure_list(results_raw)
        
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
