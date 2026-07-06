import asyncio
import uuid
import os
from minio import Minio
from backend.services.storage import ensure_bucket_exists, get_video_url, minio_client, BUCKET_NAME

ensure_bucket_exists()
with open("test.txt", "w") as f:
    f.write("hello minio")

minio_client.fput_object(BUCKET_NAME, "test.txt", "test.txt")
url = get_video_url("test.txt")
print(f"URL: {url}")
minio_client.remove_object(BUCKET_NAME, "test.txt")
os.remove("test.txt")
