"""Download all required local models on first run."""

import sys
import urllib.request
from pathlib import Path


def _get_model_dir() -> Path:
    """Return model directory, handling PyInstaller frozen bundles."""
    if getattr(sys, 'frozen', False):
        # Running inside PyInstaller bundle
        return Path(sys._MEIPASS) / "models"
    return Path(__file__).parent


MODEL_DIR = _get_model_dir()
MODELS = {
    "yolov8n.pt": "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt",
    "yolov8n-pose.pt": "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n-pose.pt",
    "emotion-ferplus-8.onnx": "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/emotion_ferplus/model/emotion-ferplus-8.onnx",
    "midas_v21_small_256.onnx": "https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx",
}


def ensure_models():
    """Download any missing model files. Skip in frozen (PyInstaller) mode."""
    if getattr(sys, 'frozen', False):
        # Models are bundled inside the PyInstaller binary — no download needed
        return
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in MODELS.items():
        path = MODEL_DIR / filename
        if not path.exists():
            try:
                print(f"Downloading {filename}...")
                urllib.request.urlretrieve(url, path)
                print(f"  -> saved to {path} ({path.stat().st_size / 1e6:.1f} MB)")
            except Exception as e:
                print(f"  -> WARNING: could not download {filename}: {e}")
                print(f"     The app will use fallback algorithms instead.")


if __name__ == "__main__":
    ensure_models()
