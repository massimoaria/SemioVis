"""Pydantic models for image upload."""

from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    image_id: str
    filename: str
    width: int
    height: int
    format: str
    file_path: str
    thumbnail_base64: str
