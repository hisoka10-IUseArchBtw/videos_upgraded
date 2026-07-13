import os
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from google import genai
from google.genai import types
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue

from backend.ai.metrics import (
    AI_REQUEST_LATENCY_SECONDS,
    AI_TOKEN_USAGE_TOTAL,
    AI_API_COST_TOTAL,
)
from backend.search.qdrant_client import get_qdrant_client, QDRANT_COLLECTION_NAME

# ---------------------------------------------------------------------------
# Gemini client for query embedding
# ---------------------------------------------------------------------------
_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ---------------------------------------------------------------------------
# Result dataclass — returned to API callers
# ---------------------------------------------------------------------------
@dataclass
class SearchResult:
    chunk_id: str
    video_id: str
    text: str
    score: float
    chunk_type: str
    start_time: float = 0.0
    end_time: float = 0.0
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Embedding helper
# ---------------------------------------------------------------------------
async def _embed_query(query: str) -> List[float]:
    """
    Embeds a search query using Gemini text-embedding-004.

    Uses RETRIEVAL_QUERY task type (distinct from RETRIEVAL_DOCUMENT used
    when indexing) as recommended by the Gemini embedding docs.
    """
    start = time.time()
    result = await _gemini.aio.models.embed_content(
        model="text-embedding-004",
        contents=query,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    duration = time.time() - start

    AI_REQUEST_LATENCY_SECONDS.labels(
        model="text-embedding-004", operation="embed_query"
    ).observe(duration)

    estimated_tokens = len(query) // 4
    AI_TOKEN_USAGE_TOTAL.labels(
        model="text-embedding-004", operation="embed_query", token_type="total"
    ).inc(estimated_tokens)
    AI_API_COST_TOTAL.labels(
        model="text-embedding-004", operation="embed_query"
    ).inc((estimated_tokens / 1_000_000) * 0.02)

    return result.embeddings[0].values


# ---------------------------------------------------------------------------
# SearchService
# ---------------------------------------------------------------------------
class SearchService:
    """
    Wraps Qdrant vector search with optional metadata filtering.

    All methods are async and share the module-level AsyncQdrantClient
    singleton — no per-request connection overhead.
    """

    async def semantic_search(
        self,
        query: str,
        video_id: Optional[str] = None,
        chunk_types: Optional[List[str]] = None,
        limit: int = 10,
        score_threshold: float = 0.3,
    ) -> List[SearchResult]:
        """
        Embed the query and retrieve the nearest chunks from Qdrant.

        Args:
            query:           Natural language search query.
            video_id:        If provided, restricts results to a single video.
            chunk_types:     List of chunk types to include, e.g. ["transcript", "summary"].
                             If None, all types are searched.
            limit:           Maximum number of results to return.
            score_threshold: Minimum cosine similarity score (0–1).

        Returns:
            List of SearchResult ordered by relevance score (descending).
        """
        query_vector = await _embed_query(query)
        qdrant = get_qdrant_client()

        # Build Qdrant payload filter
        must_conditions = []

        if video_id:
            must_conditions.append(
                FieldCondition(key="video_id", match=MatchValue(value=str(video_id)))
            )

        if chunk_types:
            must_conditions.append(
                FieldCondition(key="chunk_type", match=MatchAny(any=chunk_types))
            )

        payload_filter = Filter(must=must_conditions) if must_conditions else None

        hits = await qdrant.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=payload_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )

        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                SearchResult(
                    chunk_id=str(hit.id),
                    video_id=payload.get("video_id", ""),
                    text=payload.get("text", ""),
                    score=hit.score,
                    chunk_type=payload.get("chunk_type", "transcript"),
                    start_time=payload.get("start_time", 0.0),
                    end_time=payload.get("end_time", 0.0),
                    metadata=payload.get("metadata", {}),
                )
            )

        return results

    async def search_across_videos(
        self,
        query: str,
        video_ids: List[str],
        chunk_types: Optional[List[str]] = None,
        limit: int = 20,
        score_threshold: float = 0.3,
    ) -> List[SearchResult]:
        """
        Search across a specific set of videos (multi-video search).

        Args:
            query:     Natural language search query.
            video_ids: List of video UUIDs to scope the search.
            chunk_types: Optional filter for chunk types.
            limit:     Maximum results.
            score_threshold: Minimum similarity score.

        Returns:
            Merged, score-ordered list of SearchResult.
        """
        query_vector = await _embed_query(query)
        qdrant = get_qdrant_client()

        must_conditions = [
            FieldCondition(key="video_id", match=MatchAny(any=video_ids))
        ]
        if chunk_types:
            must_conditions.append(
                FieldCondition(key="chunk_type", match=MatchAny(any=chunk_types))
            )

        hits = await qdrant.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(must=must_conditions),
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )

        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                SearchResult(
                    chunk_id=str(hit.id),
                    video_id=payload.get("video_id", ""),
                    text=payload.get("text", ""),
                    score=hit.score,
                    chunk_type=payload.get("chunk_type", "transcript"),
                    start_time=payload.get("start_time", 0.0),
                    end_time=payload.get("end_time", 0.0),
                    metadata=payload.get("metadata", {}),
                )
            )

        return results
