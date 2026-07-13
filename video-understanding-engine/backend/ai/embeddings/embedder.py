import os
import time
import uuid
from typing import List, Optional

from google import genai
from google.genai import types
from qdrant_client.models import PointStruct
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.AI.video_chunk import VideoChunk
from backend.search.qdrant_client import get_qdrant_client, QDRANT_COLLECTION_NAME
from backend.ai.metrics import (
    AI_TOKEN_USAGE_TOTAL,
    AI_API_COST_TOTAL,
    AI_REQUEST_LATENCY_SECONDS,
)

# ---------------------------------------------------------------------------
# Gemini embedding client
# ---------------------------------------------------------------------------
_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ---------------------------------------------------------------------------
# Internal: embed a single text string → list of floats
# ---------------------------------------------------------------------------
async def _embed_text(text: str) -> List[float]:
    start = time.time()
    result = await _gemini.aio.models.embed_content(
        model="text-embedding-004",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    duration = time.time() - start

    AI_REQUEST_LATENCY_SECONDS.labels(
        model="text-embedding-004", operation="embed"
    ).observe(duration)

    estimated_tokens = len(text) // 4
    AI_TOKEN_USAGE_TOTAL.labels(
        model="text-embedding-004", operation="embed", token_type="total"
    ).inc(estimated_tokens)
    AI_API_COST_TOTAL.labels(model="text-embedding-004", operation="embed").inc(
        (estimated_tokens / 1_000_000) * 0.02
    )

    return result.embeddings[0].values


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def embed_and_store_chunks(
    db: AsyncSession,
    video_id: uuid.UUID,
    chunks: List[dict],
    chunk_type: str = "transcript",
) -> List[VideoChunk]:
    """
    Generates embeddings for a list of chunks and:
      1. Writes lightweight SQL records (VideoChunk) to PostgreSQL — no vector column.
      2. Upserts vector points with full payload into Qdrant.

    Args:
        db:          Async SQLAlchemy session.
        video_id:    UUID of the parent video.
        chunks:      List of dicts. Required keys depend on chunk_type:
                       transcript/ocr/chapter/summary →
                         {"text": str, "start_time": float, "end_time": float}
                     Optional: "metadata" dict for speaker labels, titles, etc.
        chunk_type:  One of "transcript" | "ocr" | "chapter" | "summary".

    Returns:
        List of committed VideoChunk ORM objects.
    """
    qdrant = get_qdrant_client()
    db_chunks: List[VideoChunk] = []
    qdrant_points: List[PointStruct] = []

    for i, chunk in enumerate(chunks):
        text = chunk["text"]
        start_time = chunk.get("start_time", 0.0)
        end_time = chunk.get("end_time", 0.0)
        extra_meta = chunk.get("metadata", {})

        # --- Generate embedding ---
        vector = await _embed_text(text)

        # --- SQL record (relational anchor, no embedding stored here) ---
        db_chunk = VideoChunk(
            video_id=video_id,
            chunk_index=i,
            text=text,
            chunk_type=chunk_type,
            start_time=start_time,
            end_time=end_time,
            metadata_=extra_meta if extra_meta else None,
        )
        db.add(db_chunk)
        db_chunks.append(db_chunk)

        # --- Qdrant point (vector + full payload for retrieval) ---
        # Use the Python UUID directly — Qdrant accepts UUID point IDs natively.
        qdrant_points.append(
            PointStruct(
                id=str(db_chunk.id),
                vector=vector,
                payload={
                    "video_id": str(video_id),
                    "chunk_id": str(db_chunk.id),
                    "chunk_index": i,
                    "text": text,
                    "chunk_type": chunk_type,
                    "start_time": start_time,
                    "end_time": end_time,
                    "metadata": extra_meta,
                },
            )
        )

    # Commit SQL records first so IDs are stable before Qdrant upsert
    await db.commit()

    # Batch-upsert all points into Qdrant
    if qdrant_points:
        await qdrant.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=qdrant_points,
        )

    return db_chunks


async def embed_and_store_single_chunk(
    db: AsyncSession,
    video_id: uuid.UUID,
    text: str,
    chunk_type: str,
    start_time: float = 0.0,
    end_time: float = 0.0,
    metadata: Optional[dict] = None,
) -> VideoChunk:
    """
    Convenience wrapper for indexing a single chunk (e.g. a summary or chapter).
    """
    chunks = [
        {
            "text": text,
            "start_time": start_time,
            "end_time": end_time,
            "metadata": metadata or {},
        }
    ]
    result = await embed_and_store_chunks(db, video_id, chunks, chunk_type=chunk_type)
    return result[0]
