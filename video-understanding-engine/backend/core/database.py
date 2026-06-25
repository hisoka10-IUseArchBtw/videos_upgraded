import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://user:password@localhost:5432/video_engine"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,  
    pool_recycle=3600,   
    pool_size=5,
    max_overflow=10
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False, 
    autocommit=False, 
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
