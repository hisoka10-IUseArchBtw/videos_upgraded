import os
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import require_admin
from backend.core.database import get_db
from backend.models.User.user_model import User
from backend.models.Video.video_model import Video
from backend.models.Analytics.search_log import SearchLog

router = APIRouter(prefix="/analytics", tags=["Analytics"])

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class VideoStats(BaseModel):
    total: int
    completed: int
    processing: int
    pending: int
    failed: int
    total_duration_hours: float


class PopularSearch(BaseModel):
    query: str
    count: int


class QueueStats(BaseModel):
    pending_jobs: int


class AIStats(BaseModel):
    total_tokens: float
    estimated_cost_usd: float


class AnalyticsOverview(BaseModel):
    videos: VideoStats
    queue: QueueStats
    ai: AIStats
    popular_searches: List[PopularSearch]
    generated_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_video_stats(db: AsyncSession) -> VideoStats:
    result = await db.execute(
        select(Video.status, func.count(Video.id).label("count"))
        .group_by(Video.status)
    )
    rows = result.all()
    counts = {row.status: row.count for row in rows}
    total = sum(counts.values())

    # Total duration of completed videos in hours
    dur_result = await db.execute(
        select(func.coalesce(func.sum(Video.duration), 0.0))
        .where(Video.status == "COMPLETED")
    )
    total_seconds = dur_result.scalar() or 0.0

    return VideoStats(
        total=total,
        completed=counts.get("COMPLETED", 0),
        processing=counts.get("PROCESSING", 0),
        pending=counts.get("PENDING", 0),
        failed=counts.get("FAILED", 0),
        total_duration_hours=round(total_seconds / 3600, 2),
    )


async def _get_popular_searches(db: AsyncSession, limit: int = 5) -> List[PopularSearch]:
    result = await db.execute(
        select(SearchLog.query, func.count(SearchLog.id).label("count"))
        .group_by(SearchLog.query)
        .order_by(func.count(SearchLog.id).desc())
        .limit(limit)
    )
    return [PopularSearch(query=row.query, count=row.count) for row in result.all()]


async def _get_queue_stats() -> QueueStats:
    try:
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        # Celery uses a list key named "celery" by default
        pending = await r.llen("celery")
        await r.aclose()
        return QueueStats(pending_jobs=pending)
    except Exception as e:
        print(f"Redis error: {e}")
        return QueueStats(pending_jobs=-1)


async def _get_ai_stats() -> AIStats:
    total_tokens = 0.0
    estimated_cost = 0.0
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Query Prometheus for cumulative token usage
            token_resp = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": "sum(ai_token_usage_total)"},
            )
            if token_resp.status_code == 200:
                data = token_resp.json()
                results = data.get("data", {}).get("result", [])
                if results:
                    total_tokens = float(results[0]["value"][1])

            # Query Prometheus for cumulative cost
            cost_resp = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": "sum(ai_api_cost_total)"},
            )
            if cost_resp.status_code == 200:
                data = cost_resp.json()
                results = data.get("data", {}).get("result", [])
                if results:
                    estimated_cost = float(results[0]["value"][1])
    except Exception as e:
        print(f"Prometheus query error: {e}")

    return AIStats(
        total_tokens=total_tokens,
        estimated_cost_usd=round(estimated_cost, 6),
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/overview",
    response_model=AnalyticsOverview,
    status_code=status.HTTP_200_OK,
    summary="Aggregated analytics dashboard overview",
    description=(
        "Returns an aggregated analytics snapshot including video processing stats, "
        "Redis queue depth, AI token & cost usage from Prometheus, and the top-5 "
        "most popular search queries."
    ),
)
async def get_analytics_overview(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverview:
    video_stats, popular, queue, ai = await _get_video_stats(db), \
        await _get_popular_searches(db), \
        await _get_queue_stats(), \
        await _get_ai_stats()

    return AnalyticsOverview(
        videos=video_stats,
        queue=queue,
        ai=ai,
        popular_searches=popular,
        generated_at=datetime.utcnow().isoformat() + "Z",
    )
