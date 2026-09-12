import os
import re
import uuid
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Allowed image MIME types and extensions
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/svg+xml",
    "image/gif"
}

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB max

class S3StorageService:
    @staticmethod
    def is_s3_configured() -> bool:
        """Check if live AWS S3 credentials and bucket are configured."""
        return bool(
            settings.AWS_ACCESS_KEY_ID 
            and settings.AWS_SECRET_ACCESS_KEY 
            and settings.AWS_S3_BUCKET_NAME
        )

    @classmethod
    def get_s3_client(cls):
        """Create authenticated boto3 S3 client."""
        import boto3
        from botocore.config import Config

        client_kwargs = {
            "service_name": "s3",
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "region_name": settings.AWS_REGION or "us-east-1",
            "config": Config(signature_version="s3v4")
        }
        if settings.AWS_S3_ENDPOINT_URL:
            client_kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL

        return boto3.client(**client_kwargs)

    @classmethod
    async def upload_image(
        cls, 
        file: UploadFile, 
        category: str = "companies"
    ) -> Dict[str, Any]:
        """
        Validate, sanitize, and upload an image attachment to AWS S3 (or local media fallback).
        """
        raw_filename = file.filename or "upload.png"
        ext = Path(raw_filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension '{ext}'. Allowed formats: PNG, JPG, JPEG, WEBP, SVG, GIF."
            )

        # Read contents and check size
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of 5MB ({file_size / (1024 * 1024):.1f}MB uploaded)."
            )

        # Content Type Validation
        content_type = file.content_type or mimetypes.guess_type(raw_filename)[0] or "image/png"
        if content_type.lower() not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image MIME type '{content_type}'. Must be a valid image."
            )

        # Generate unique collision-free filename
        clean_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(raw_filename).stem)[:30]
        unique_token = uuid.uuid4().hex[:10]
        stored_filename = f"{clean_base}_{unique_token}{ext}"
        s3_key = f"logos/{category}/{stored_filename}"

        # -------------------------------------------------------------
        # 1. AWS S3 Upload (if configured)
        # -------------------------------------------------------------
        if cls.is_s3_configured():
            try:
                s3_client = cls.get_s3_client()
                bucket = settings.AWS_S3_BUCKET_NAME

                s3_client.put_object(
                    Bucket=bucket,
                    Key=s3_key,
                    Body=content,
                    ContentType=content_type,
                )

                if settings.AWS_S3_CUSTOM_DOMAIN:
                    domain = settings.AWS_S3_CUSTOM_DOMAIN.strip().rstrip('/')
                    if not domain.startswith("http://") and not domain.startswith("https://"):
                        domain = f"https://{domain}"
                    public_url = f"{domain}/{s3_key}"
                else:
                    public_url = f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

                logger.info(f"Successfully uploaded logo to AWS S3: {public_url}")
                return {
                    "url": public_url,
                    "filename": stored_filename,
                    "key": s3_key,
                    "size": file_size,
                    "content_type": content_type,
                    "storage": "s3"
                }

            except Exception as e:
                logger.error(f"AWS S3 upload error: {e}. Falling back to local media storage.")
                # Fallback to local storage if AWS S3 network/auth error occurs

        # -------------------------------------------------------------
        # 2. Local Media Storage Fallback
        # -------------------------------------------------------------
        backend_root = Path(__file__).resolve().parent.parent.parent.parent
        media_dir = backend_root / "media" / "uploads" / "logos" / category
        media_dir.mkdir(parents=True, exist_ok=True)

        destination_path = media_dir / stored_filename
        with open(destination_path, "wb") as f:
            f.write(content)

        relative_url = f"/media/uploads/logos/{category}/{stored_filename}"
        base_url = (settings.BACKEND_URL or "http://127.0.0.1:8000").strip().rstrip('/')
        public_url = f"{base_url}{relative_url}"

        logger.info(f"Saved logo to local storage: {public_url}")
        return {
            "url": public_url,
            "filename": stored_filename,
            "key": s3_key,
            "size": file_size,
            "content_type": content_type,
            "storage": "local"
        }
