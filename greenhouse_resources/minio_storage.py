"""Хранение изображений и видео ресурсов в Minio."""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from minio import Minio

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "root")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "rootpassword")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "greenhouse")
MINIO_BASE_URL = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}"

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)


def build_minio_url(file_key):
    return f"{MINIO_BASE_URL}/{file_key}"


def upload_resource_file(file: UploadFile, prefix: str) -> str:
    """Сохраняет файл в Minio под сгенерированным латинским именем
    (например greenhouse_image_3f9c1a2b7d4e.jpg) и возвращает его url."""
    extension = Path(file.filename or "").suffix.lower()
    file_key = f"greenhouse_{prefix}_{uuid.uuid4().hex[:12]}{extension}"
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    minio_client.put_object(
        MINIO_BUCKET, file_key, file.file, size,
        content_type=file.content_type or "application/octet-stream",
    )
    return build_minio_url(file_key)
