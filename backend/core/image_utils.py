"""Image loading, resizing, and normalisation utilities."""

import base64
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

UPLOAD_DIR = Path("/tmp/semiovis_uploads")


def load_image(image_id: str) -> np.ndarray:
    """Load an uploaded image by ID, return as RGB numpy array."""
    matches = list(UPLOAD_DIR.glob(f"{image_id}.*"))
    if not matches:
        raise FileNotFoundError(f"Image not found: {image_id}")
    img = cv2.imread(str(matches[0]))
    if img is None:
        raise ValueError(f"Failed to read image: {matches[0]}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def to_grayscale(img_rgb: np.ndarray) -> np.ndarray:
    """Convert RGB image to grayscale."""
    return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)


def resize_if_needed(img: np.ndarray, max_dim: int = 2000) -> np.ndarray:
    """Downsample if any dimension exceeds max_dim."""
    h, w = img.shape[:2]
    if max(h, w) <= max_dim:
        return img
    scale = max_dim / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def image_to_base64(img_rgb: np.ndarray, quality: int = 85) -> str:
    """Encode RGB numpy array as JPEG base64 string."""
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf.tobytes()).decode()


def get_image_path(image_id: str) -> Path:
    """Resolve the file path for an uploaded image."""
    matches = list(UPLOAD_DIR.glob(f"{image_id}.*"))
    if not matches:
        raise FileNotFoundError(f"Image not found: {image_id}")
    return matches[0]
