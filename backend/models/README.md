# Local ML Model Weights

These models are auto-downloaded on first run by `download_models.py`.

| Model | File | Size | Purpose |
|---|---|---|---|
| YOLOv8n | yolov8n.pt | ~6MB | Object detection, participants |
| YOLOv8n-pose | yolov8n-pose.pt | ~7MB | Body bbox, social distance, pose |
| FER+ emotion | emotion-ferplus-8.onnx | ~34MB | 7 basic emotions per face |
| MiDaS v2.1 small | midas_v21_small_256.onnx | ~5MB | Monocular depth estimation |

MediaPipe Face Mesh (~2MB) is bundled with the `mediapipe` Python package.

Total: ~55MB. All models are open-source with permissive licenses.
