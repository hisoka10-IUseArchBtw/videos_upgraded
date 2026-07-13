import os
import json
import time
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from google import genai
from google.genai import types

from backend.models.AI.chapter import Chapter
from backend.ai.prompts.chapter_prompt import CHAPTER_PROMPT
from backend.ai.metrics import AI_REQUEST_LATENCY_SECONDS, AI_TOKEN_USAGE_TOTAL, AI_API_COST_TOTAL

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_and_store_chapters(db: AsyncSession, video_id: str, transcript_chunks: List[Dict]) -> List[Chapter]:
    if not transcript_chunks:
        return []

    # Format the chunks as a JSON string
    transcript_json = json.dumps(transcript_chunks, indent=2)
    prompt = CHAPTER_PROMPT.format(transcript_json=transcript_json)

    start_time = time.time()
    response = await client.aio.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2, # Low temperature for structured output
        )
    )
    duration = time.time() - start_time

    # Record metrics
    AI_REQUEST_LATENCY_SECONDS.labels(model="gemini-1.5-flash", operation="generate_chapters").observe(duration)
    
    # Estimate tokens
    estimated_tokens = len(prompt) // 4
    AI_TOKEN_USAGE_TOTAL.labels(model="gemini-1.5-flash", operation="generate_chapters", token_type="prompt").inc(estimated_tokens)
    AI_API_COST_TOTAL.labels(model="gemini-1.5-flash", operation="generate_chapters").inc((estimated_tokens / 1_000_000) * 0.075)

    chapters_data = []
    try:
        chapters_data = json.loads(response.text)
    except Exception as e:
        print(f"Failed to parse Gemini chapter response: {e}")
        return []

    created_chapters = []
    for ch_data in chapters_data:
        chapter = Chapter(
            video_id=video_id,
            title=ch_data.get("title", "Untitled Chapter"),
            summary=ch_data.get("summary", ""),
            start_time=float(ch_data.get("start_time", 0.0)),
            end_time=float(ch_data.get("end_time", 0.0))
        )
        db.add(chapter)
        created_chapters.append(chapter)

    await db.commit()
    for ch in created_chapters:
        await db.refresh(ch)
        
    return created_chapters
