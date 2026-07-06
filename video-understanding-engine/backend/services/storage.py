import os
import uuid
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile
from datetime import timedelta

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "videos")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
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
        url = minio_client.presigned_get_object(
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
