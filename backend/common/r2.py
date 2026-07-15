import logging
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from auth.dependencies import get_current_user_id
from common.config import get_settings
from common.response import CustomResponse

logger = logging.getLogger(__name__)

settings = get_settings()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/ogg", "video/quicktime"}
ALLOWED_MEDIA_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES

MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB

PRESIGN_EXPIRY = 300  # seconds


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ENDPOINT_HOST}",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def _generate_presigned_put(content_type: str, folder: str, size: int) -> dict:
    key = f"{folder}/{uuid.uuid4()}"
    client = _s3_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.R2_BUCKET,
            "Key": key,
            "ContentType": content_type,
            "ContentLength": size,
        },
        ExpiresIn=PRESIGN_EXPIRY,
    )
    public_url = f"{settings.R2_PUBLIC_URL}/{key}"
    return {"upload_url": url, "key": key, "public_url": public_url, "expires_in": PRESIGN_EXPIRY}



class ImageUploadRequest(BaseModel):
    content_type: str = Field(..., description="MIME type of the image")
    size: int = Field(..., ge=1, le=MAX_IMAGE_SIZE, description="File size in bytes")
    folder: str = Field("images", max_length=64, pattern=r"^[a-zA-Z0-9_/-]+$")

    @field_validator("content_type")
    @classmethod
    def validate_image_type(cls, v: str) -> str:
        if v not in ALLOWED_IMAGE_TYPES:
            raise ValueError(f"content_type must be one of: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}")
        return v


class VideoUploadRequest(BaseModel):
    content_type: str = Field(..., description="MIME type of the video")
    size: int = Field(..., ge=1, le=MAX_VIDEO_SIZE, description="File size in bytes")
    folder: str = Field("videos", max_length=64, pattern=r"^[a-zA-Z0-9_/-]+$")

    @field_validator("content_type")
    @classmethod
    def validate_video_type(cls, v: str) -> str:
        if v not in ALLOWED_VIDEO_TYPES:
            raise ValueError(f"content_type must be one of: {', '.join(sorted(ALLOWED_VIDEO_TYPES))}")
        return v


class MediaUploadRequest(BaseModel):
    content_type: str = Field(..., description="MIME type — image or video")
    size: int = Field(..., ge=1, description="File size in bytes")
    folder: str = Field("media", max_length=64, pattern=r"^[a-zA-Z0-9_/-]+$")

    @field_validator("content_type")
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        if v not in ALLOWED_MEDIA_TYPES:
            raise ValueError(f"content_type must be one of: {', '.join(sorted(ALLOWED_MEDIA_TYPES))}")
        return v

    @field_validator("size")
    @classmethod
    def validate_size(cls, v: int, info) -> int:
        limit = MAX_IMAGE_SIZE if info.data.get("content_type") in ALLOWED_IMAGE_TYPES else MAX_VIDEO_SIZE
        if v > limit:
            raise ValueError(f"size exceeds limit of {limit} bytes")
        return v



router = APIRouter(
    prefix="/upload", tags=["upload"], dependencies=[Depends(get_current_user_id)]
)


def _presign_response(body) -> dict:
    try:
        data = _generate_presigned_put(body.content_type, body.folder, body.size)
        return CustomResponse.success(data=data, message="Presigned URL generated")
    except ClientError:
        logger.exception("Presigned URL generation failed")
        return CustomResponse.error(message="Upload service unavailable", status_code=500)


@router.post("/image/presigned-url")
def presigned_image_url(body: ImageUploadRequest):
    return _presign_response(body)


@router.post("/video/presigned-url")
def presigned_video_url(body: VideoUploadRequest):
    return _presign_response(body)


@router.post("/media/presigned-url")
def presigned_media_url(body: MediaUploadRequest):
    return _presign_response(body)
