import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.auth.jwt import get_current_user
from backend.models.User.user_model import User
from backend.models.Video.video_model import Video
from backend.models.Analytics.search_log import SearchLog
from backend.search.service import SearchService, SearchResult
from sqlalchemy.future import select

router = APIRouter(prefix="/search", tags=["Semantic Search"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Natural language search query")
    video_id: Optional[uuid.UUID] = Field(None, description="Scope search to a single video")
    chunk_types: Optional[List[str]] = Field(
        None,
        description="Filter by chunk type. Valid values: transcript, ocr, chapter, summary",
        examples=[["transcript", "summary"]],
    )
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results (1–50)")
    score_threshold: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum similarity score (0–1)"
    )


class SearchResultResponse(BaseModel):
    chunk_id: str
    video_id: str
    text: str
    score: float
    chunk_type: str
    start_time: float
    end_time: float
    metadata: dict

    @classmethod
    def from_result(cls, r: SearchResult) -> "SearchResultResponse":
        return cls(
            chunk_id=r.chunk_id,
            video_id=r.video_id,
            text=r.text,
            score=round(r.score, 4),
            chunk_type=r.chunk_type,
            start_time=r.start_time,
            end_time=r.end_time,
            metadata=r.metadata,
        )


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
VALID_CHUNK_TYPES = {"transcript", "ocr", "chapter", "summary"}


@router.post(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search across video content",
    description=(
        "Embeds the query using Gemini text-embedding-004 and retrieves the "
        "most semantically similar chunks from Qdrant. Supports filtering by "
        "video and chunk type, with timestamp retrieval for every result."
    ),
)
async def semantic_search(
    body: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """
    POST /search

    Body:
    ```json
    {
        "query": "gradient descent",
        "video_id": "...",          // optional
        "chunk_types": ["transcript"],  // optional
        "limit": 10,
        "score_threshold": 0.3
    }
    ```
    """
    # Validate chunk_types if provided
    if body.chunk_types:
        invalid = set(body.chunk_types) - VALID_CHUNK_TYPES
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid chunk_types: {invalid}. Valid values: {VALID_CHUNK_TYPES}",
            )

    service = SearchService()

    try:
        if body.video_id:
            # Verify ownership
            result = await db.execute(
                select(Video).where(Video.id == body.video_id, Video.user_id == current_user.user_id)
            )
            if not result.scalars().first():
                raise HTTPException(status_code=403, detail="Not authorized to search this video")
                
            results = await service.semantic_search(
                query=body.query,
                video_id=str(body.video_id),
                chunk_types=body.chunk_types,
                limit=body.limit,
                score_threshold=body.score_threshold,
            )
        else:
            # Get all user's video IDs
            v_res = await db.execute(select(Video.id).where(Video.user_id == current_user.user_id))
            user_video_ids = [str(v_id) for v_id in v_res.scalars().all()]
            
            if not user_video_ids:
                results = []
            else:
                results = await service.search_across_videos(
                    query=body.query,
                    video_ids=user_video_ids,
                    chunk_types=body.chunk_types,
                    limit=body.limit,
                    score_threshold=body.score_threshold,
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search service unavailable: {str(e)}",
        )

    results = [SearchResultResponse.from_result(r) for r in results]
    
    # Log the search query asynchronously
    try:
        log = SearchLog(
            user_id=current_user.user_id,
            query=body.query,
            result_count=len(results),
        )
        db.add(log)
        await db.commit()
    except Exception as e:
        print(f"Failed to log search query: {e}")

    return SearchResponse(
        query=body.query,
        total=len(results),
        results=results,
    )
