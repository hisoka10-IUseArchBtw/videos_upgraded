from typing import List
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.database import get_db
from backend.models.User.user_model import User
from backend.models.Video.video_model import Video
from backend.models.Video.video_schema import VideoResponse
from backend.auth.jwt import get_current_user
from backend.services.storage import upload_video_file
from backend.workers.video_worker import process_video_task

router = APIRouter(tags=["Video"], prefix="/video")

@router.post('/upload', response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File provided is not a video")

    # Create Video record with PENDING status
    new_video = Video(
        user_id=current_user.user_id,
        title=file.filename,
        filename=file.filename,
        status="PENDING"
    )
    db.add(new_video)
    await db.commit()
    await db.refresh(new_video)

    try:
        # Upload file to storage (MinIO)
        object_name = await upload_video_file(file, current_user.user_id, new_video.id)
        
        # We can update the filename to the MinIO object name if we want
        new_video.filename = object_name
        await db.commit()
        await db.refresh(new_video)
    except Exception as e:
        # If upload fails, we might want to mark the video as FAILED
        new_video.status = "FAILED"
        await db.commit()
        raise HTTPException(status_code=500, detail="Failed to upload video to storage")

    # Enqueue Celery Task
    process_video_task.delay(str(new_video.id))

    return new_video

@router.get('/list', response_model=List[VideoResponse])
async def list_videos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Video).where(Video.user_id == current_user.user_id))
    videos = result.scalars().all()
    return videos

@router.get('/{video_id}', response_model=VideoResponse)
async def get_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Video).where(Video.id == video_id, Video.user_id == current_user.user_id)
    )
    video = result.scalars().first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video
