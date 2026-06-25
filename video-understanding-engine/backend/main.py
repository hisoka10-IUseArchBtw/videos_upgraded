from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .core.database import Base, engine

# Import all models here so SQLAlchemy registers them before create_all
from .models.User.user_model import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    print("Shutting down")

from .api import signup

app = FastAPI(lifespan=lifespan)
app.include_router(signup.router)

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