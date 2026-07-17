from typing import List
import uuid
import hashlib
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.database import get_db
from backend.models.User.user_model import User
from backend.models.Video.video_model import Video
from backend.models.Video.video_schema import VideoResponse, VideoWithThumbnail
from backend.auth.jwt import get_current_user
from backend.services.storage import upload_video_file, get_video_url, delete_video_assets, get_thumbnail_url
from backend.workers.video_worker import process_video_task
from backend.services.video_recycler import recycle_video
from backend.search.qdrant_client import get_qdrant_client, QDRANT_COLLECTION_NAME
from qdrant_client.models import Filter, FieldCondition, MatchValue

router = APIRouter(tags=["Video"], prefix="/video")

@router.post('/upload', response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File provided is not a video")

    # Read the file content to compute SHA-256
    file_content = await file.read()
    sha256_hash = hashlib.sha256(file_content).hexdigest()
    # Seek back to start so MinIO can read it if needed
    await file.seek(0)

    # Check if a video with this SHA-256 already exists and is COMPLETED
    existing_video_result = await db.execute(
        select(Video).where(Video.sha256 == sha256_hash, Video.status == "COMPLETED").limit(1)
    )
    existing_video = existing_video_result.scalars().first()

    if existing_video:
        # Deduplicate
        new_video = Video(
            user_id=current_user.user_id,
            title=file.filename,
            filename=existing_video.filename, # Share the MinIO object name
            status="COMPLETED",
            duration=existing_video.duration,
            resolution=existing_video.resolution,
            fps=existing_video.fps,
            codec=existing_video.codec,
            sha256=sha256_hash
        )
        db.add(new_video)
        await db.commit()
        await db.refresh(new_video)
        
        # Recycle AI data
        await recycle_video(db, existing_video.id, new_video.id)
        
        return new_video

    # Create Video record with PENDING status
    new_video = Video(
        user_id=current_user.user_id,
        title=file.filename,
        filename=file.filename,
        status="PENDING",
        sha256=sha256_hash
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

@router.get('/list', response_model=List[VideoWithThumbnail])
async def list_videos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Video).where(Video.user_id == current_user.user_id))
    videos = result.scalars().all()
    out = []
    for v in videos:
        thumbnail_url = await asyncio.to_thread(get_thumbnail_url, v.id)
        out.append(VideoWithThumbnail(
            id=v.id,
            user_id=v.user_id,
            title=v.title,
            filename=v.filename,
            status=v.status,
            created_at=v.created_at,
            duration=v.duration,
            thumbnail_url=thumbnail_url,
        ))
    return out

@router.get('/{video_id}', response_model=VideoWithThumbnail)
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
    
    thumbnail_url = await asyncio.to_thread(get_thumbnail_url, video.id)
    return VideoWithThumbnail(
        id=video.id,
        user_id=video.user_id,
        title=video.title,
        filename=video.filename,
        status=video.status,
        created_at=video.created_at,
        duration=video.duration,
        thumbnail_url=thumbnail_url,
    )

@router.get('/{video_id}/url')
async def get_video_presigned_url(
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
    
    url = get_video_url(video.filename)
    return {"url": url}

@router.delete('/{video_id}', status_code=status.HTTP_200_OK)
async def delete_video(
    video_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch video record and verify ownership
    result = await db.execute(
        select(Video).where(Video.id == video_id, Video.user_id == current_user.user_id)
    )
    video = result.scalars().first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # 2. Check if other videos reference the same filename (due to deduplication)
    same_file_count_result = await db.execute(
        select(Video).where(Video.filename == video.filename, Video.id != video.id)
    )
    other_references = same_file_count_result.first()
    other_references_exist = other_references is not None

    # 3. Delete files from MinIO (video file if no other references, plus all frames)
    await asyncio.to_thread(delete_video_assets, video.id, video.filename, other_references_exist)

    # 4. Delete vector chunks from Qdrant
    qdrant = get_qdrant_client()
    try:
        await qdrant.delete(
            collection_name=QDRANT_COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="video_id",
                        match=MatchValue(value=str(video_id))
                    )
                ]
            )
        )
    except Exception as e:
        print(f"Error deleting vectors from Qdrant: {e}")

    # 5. Delete video row from SQL (cascade deletes related tables like video_chunks, chapters, etc.)
    await db.delete(video)
    await db.commit()

    return {"message": "Video successfully deleted", "video_id": video_id}
