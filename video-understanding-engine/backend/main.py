from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .core.database import Base, engine

# Import all models so SQLAlchemy registers them before create_all
from .models.User.user_model import User
from .models.Video.video_model import Video
from .models.AI import VideoAnalysis, Flashcard, QuizQuestion, VideoChunk
from .models.AI.chapter import Chapter
from .models.Analytics.search_log import SearchLog

# Routers
from .api import signup, login, video, analytics
from .ai.routing import analysis
from .chat import router as chat_router
from .search import router as search_router
from .search.qdrant_client import ensure_collection

from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up")

    # Create / migrate PostgreSQL tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure Qdrant collection exists (idempotent)
    await ensure_collection()

    yield
    print("Shutting down")


app = FastAPI(
    title="Video Understanding Engine",
    description="Production-grade AI platform for understanding long-form videos.",
    version="0.6.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

app.include_router(signup.router)
app.include_router(login.router)
app.include_router(video.router)
app.include_router(analysis.router)
app.include_router(chat_router.router)
app.include_router(search_router)
app.include_router(analytics.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )