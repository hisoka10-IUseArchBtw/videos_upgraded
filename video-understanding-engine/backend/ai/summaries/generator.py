import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.AI.video_analysis import VideoAnalysis
from backend.ai.prompts import SUMMARY_PROMPT
from backend.ai.providers.gemini import GeminiProvider

async def generate_and_store_summary(db: AsyncSession, video_id: uuid.UUID, transcript: str):
    provider = GeminiProvider()
    
    # Generate summary JSON
    result = await provider.generate_json(SUMMARY_PROMPT, transcript=transcript)
    
    # Parse results
    summary = result.get("summary", "")
    key_topics = result.get("key_topics", [])
    
    # Store in DB
    analysis = VideoAnalysis(
        video_id=video_id,
        summary=summary,
        key_topics=key_topics
    )
    db.add(analysis)
    
    return analysis
