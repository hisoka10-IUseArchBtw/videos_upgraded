import os
import uuid
import time
import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.AI.video_chunk import VideoChunk
from backend.ai.metrics import AI_TOKEN_USAGE_TOTAL, AI_API_COST_TOTAL, AI_REQUEST_LATENCY_SECONDS

# Initialize Gemini Client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def embed_and_store_chunks(db: AsyncSession, video_id: uuid.UUID, transcript_chunks: list[dict]):
    """
    Generates embeddings for transcript chunks and stores them in the database.
    
    Expected format for transcript_chunks:
    [
        {"text": "spoken text here", "start_time": 0.0, "end_time": 5.5},
        ...
    ]
    """
    db_chunks = []
    
    for i, chunk in enumerate(transcript_chunks):
        text = chunk["text"]
        
        # Call Gemini embedding model
        # Using the recommended model for text embeddings
        start_time = time.time()
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
        )
        duration = time.time() - start_time
        
        # Track latency
        AI_REQUEST_LATENCY_SECONDS.labels(model="text-embedding-004", operation="embed").observe(duration)
        
        # Track tokens & cost (Rough estimation: 1 token ~ 4 chars for english)
        estimated_tokens = len(text) // 4
        AI_TOKEN_USAGE_TOTAL.labels(model="text-embedding-004", operation="embed", token_type="total").inc(estimated_tokens)
        
        # Cost estimate: text-embedding-004 costs ~$0.02 per 1M tokens
        estimated_cost = (estimated_tokens / 1_000_000) * 0.02
        AI_API_COST_TOTAL.labels(model="text-embedding-004", operation="embed").inc(estimated_cost)
        
        embedding = result["embedding"]
        
        # Create DB record
        db_chunk = VideoChunk(
            video_id=video_id,
            chunk_index=i,
            text=text,
            embedding=embedding,
            start_time=chunk["start_time"],
            end_time=chunk["end_time"]
        )
        db_chunks.append(db_chunk)
        db.add(db_chunk)
    
    # Commit all chunks to the database
    await db.commit()
    
    return db_chunks
