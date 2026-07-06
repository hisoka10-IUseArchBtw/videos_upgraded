from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .core.database import Base, engine

# Import all models here so SQLAlchemy registers them before create_all
from .models.User.user_model import User
from .models.Video.video_model import Video
from .models.AI import VideoAnalysis, Flashcard, QuizQuestion, VideoChunk

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    print("Shutting down")

from .api import signup, login, video
from .ai.routing import analysis
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(lifespan=lifespan)
Instrumentator().instrument(app).expose(app)

app.include_router(signup.router)
app.include_router(login.router)
app.include_router(video.router)
app.include_router(analysis.router)

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