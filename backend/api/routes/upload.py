"""POST /api/upload — Image upload endpoint."""

import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image

from api.models.image import ImageUploadResponse

router = APIRouter()

UPLOAD_DIR = Path("/tmp/semiovis_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff", "image/bmp"}
MAX_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """Upload an image for analysis."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(400, "File too large (max 50 MB)")

    image_id = str(uuid.uuid4())
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    save_path = UPLOAD_DIR / f"{image_id}{ext}"
    save_path.write_bytes(data)

    img = Image.open(save_path)
    width, height = img.size
    fmt = img.format or ext.lstrip(".")

    # Generate thumbnail as base64
    import base64
    from io import BytesIO

    thumb = img.copy()
    thumb.thumbnail((256, 256))
    buf = BytesIO()
    thumb.save(buf, format="JPEG")
    thumbnail_base64 = base64.b64encode(buf.getvalue()).decode()

    return ImageUploadResponse(
        image_id=image_id,
        filename=file.filename or "image.jpg",
        width=width,
        height=height,
        format=fmt,
        file_path=str(save_path),
        thumbnail_base64=thumbnail_base64,
    )
