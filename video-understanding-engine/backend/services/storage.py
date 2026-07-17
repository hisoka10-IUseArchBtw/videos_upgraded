import os
import uuid
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
from datetime import timedelta

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_EXTERNAL_ENDPOINT = os.getenv("MINIO_EXTERNAL_ENDPOINT", MINIO_ENDPOINT)
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
# Presigned URLs go through Caddy (HTTPS), so external client uses TLS=true by default
MINIO_EXTERNAL_SECURE = os.getenv("MINIO_EXTERNAL_SECURE", "true").lower() == "true"
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "videos")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
    region=MINIO_REGION
)

presigned_client = Minio(
    MINIO_EXTERNAL_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_EXTERNAL_SECURE,
    region=MINIO_REGION
)

def ensure_bucket_exists():
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
    except S3Error as e:
        print(f"Error checking/creating bucket: {e}")

async def upload_video_file(file: UploadFile, user_id: uuid.UUID, video_id: uuid.UUID) -> str:
    """
    Uploads a video file to MinIO and returns the object name.
    """
    ensure_bucket_exists()
    
    # Store with a path-like structure: user_id/video_id_original_filename
    extension = os.path.splitext(file.filename)[1] if file.filename else ""
    object_name = f"{user_id}/{video_id}{extension}"
    
    # Minio's put_object can take a file-like object
    # Read the file to get its size for minio client
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    try:
        minio_client.put_object(
            BUCKET_NAME,
            object_name,
            file.file,
            length=file_size,
            content_type=file.content_type
        )
        return object_name
    except S3Error as e:
        print(f"Error uploading to MinIO: {e}")
        raise e

def get_video_url(object_name: str, expires_in_days: int = 7) -> str:
    """
    Generates a presigned URL for downloading or streaming a video file.
    """
    try:
        url = presigned_client.presigned_get_object(
            BUCKET_NAME,
            object_name,
            expires=timedelta(days=expires_in_days),
        )
        return url
    except S3Error as e:
        print(f"Error generating presigned URL: {e}")
        return ""

def delete_video_file(object_name: str) -> bool:
    """
    Deletes a video file from MinIO.
    """
    try:
        minio_client.remove_object(BUCKET_NAME, object_name)
        return True
    except S3Error as e:
        print(f"Error deleting from MinIO: {e}")
        return False

def download_video_file(object_name: str, file_path: str) -> bool:
    """
    Downloads a video file from MinIO to the specified local path.
    """
    try:
        minio_client.fget_object(BUCKET_NAME, object_name, file_path)
        return True
    except S3Error as e:
        print(f"Error downloading from MinIO: {e}")
        return False

def upload_local_file(local_path: str, object_name: str) -> bool:
    """
    Uploads a local file from the disk to MinIO.
    """
    ensure_bucket_exists()
    try:
        minio_client.fput_object(BUCKET_NAME, object_name, local_path)
        return True
    except S3Error as e:
        print(f"Error uploading local file to MinIO: {e}")
        return False

def get_thumbnail_url(video_id: uuid.UUID, expires_in_days: int = 7) -> str | None:
    """
    Generates a presigned URL for the first extracted frame (thumbnail) of a video.
    Returns None if the thumbnail doesn't exist yet.
    """
    object_name = f"frames/{video_id}/frame_0001.jpg"
    try:
        # Check if object exists before generating presigned URL
        minio_client.stat_object(BUCKET_NAME, object_name)
        url = presigned_client.presigned_get_object(
            BUCKET_NAME,
            object_name,
            expires=timedelta(days=expires_in_days),
        )
        return url
    except S3Error:
        return None

def delete_video_assets(video_id: uuid.UUID, filename: str, other_references_exist: bool) -> bool:
    """
    Deletes the original video file (if other_references_exist is False)
    and all associated frames from MinIO.
    """
    success = True
    
    # 1. Delete original video file if no other videos reference it
    if not other_references_exist:
        try:
            minio_client.remove_object(BUCKET_NAME, filename)
            print(f"Deleted video file {filename} from MinIO")
        except S3Error as e:
            print(f"Error deleting video file from MinIO: {e}")
            success = False

    # 2. Delete all frames associated with this video ID
    try:
        prefix = f"frames/{video_id}/"
        objects = minio_client.list_objects(BUCKET_NAME, prefix=prefix, recursive=True)
        for obj in objects:
            minio_client.remove_object(BUCKET_NAME, obj.object_name)
        print(f"Deleted frames with prefix {prefix} from MinIO")
    except S3Error as e:
        print(f"Error deleting frames from MinIO: {e}")
        success = False
        
    return success
