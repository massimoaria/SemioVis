"""Local ML models — full offline inference without API keys.

Face detection uses a priority cascade:
1. MediaPipe Face Mesh (468 landmarks, best quality) — requires Python ≤ 3.12
2. OpenCV DNN YuNet face detector (fast, works on any Python) — fallback
3. OpenCV Haar Cascade (basic, always available) — last resort
"""

from pathlib import Path

import cv2
import numpy as np

MODEL_DIR = Path(__file__).parent.parent / "models"


class LocalModels:
    """Loaded once at app startup. Provides YOLO + face detection + FER+ inference."""

    def __init__(self):
        self._yolo_detect = None
        self._yolo_pose = None
        self._face_detector = None    # "mediapipe", "yunet", or "haar"
        self._face_mesh = None        # MediaPipe Face Mesh (if available)
        self._yunet = None            # OpenCV YuNet DNN (if available)
        self._haar_cascade = None     # OpenCV Haar cascade (always available)
        self._emotion_session = None

    def load(self):
        """Load all models. Called during FastAPI lifespan startup."""
        import onnxruntime as ort

        # --- YOLO ---
        try:
            from ultralytics import YOLO
            yolo_detect_path = MODEL_DIR / "yolov8n.pt"
            yolo_pose_path = MODEL_DIR / "yolov8n-pose.pt"
            if yolo_detect_path.exists():
                self._yolo_detect = YOLO(str(yolo_detect_path))
                print(f"  YOLO detect loaded: {yolo_detect_path.name}")
            if yolo_pose_path.exists():
                self._yolo_pose = YOLO(str(yolo_pose_path))
                print(f"  YOLO pose loaded: {yolo_pose_path.name}")
        except Exception as e:
            print(f"  WARNING: YOLO load failed: {e}")

        # --- Face detection: try MediaPipe first, then YuNet, then Haar ---
        self._face_detector = self._init_face_detector()

        # --- Emotion recognition: FER+ ONNX ---
        emotion_path = MODEL_DIR / "emotion-ferplus-8.onnx"
        if emotion_path.exists():
            self._emotion_session = ort.InferenceSession(str(emotion_path))
            print(f"  FER+ emotion model loaded: {emotion_path.name}")

    def _init_face_detector(self) -> str:
        """Initialize the best available face detector."""
        # 1. Try MediaPipe
        try:
            import mediapipe as mp
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=20,
                refine_landmarks=True,
                min_detection_confidence=0.5,
            )
            print("  Face detector: MediaPipe Face Mesh (468 landmarks)")
            return "mediapipe"
        except Exception as e:
            print(f"  MediaPipe not available ({e}), trying YuNet...")

        # 2. Try OpenCV YuNet DNN face detector
        yunet_path = MODEL_DIR / "face_detection_yunet.onnx"
        if not yunet_path.exists():
            self._download_yunet(yunet_path)
        if yunet_path.exists():
            try:
                self._yunet = cv2.FaceDetectorYN.create(
                    str(yunet_path), "", (320, 320),
                    score_threshold=0.5,
                    nms_threshold=0.3,
                    top_k=20,
                )
                print(f"  Face detector: OpenCV YuNet DNN ({yunet_path.name})")
                return "yunet"
            except Exception as e:
                print(f"  YuNet not available ({e}), falling back to Haar...")

        # 3. Haar Cascade (always available in OpenCV)
        haar_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._haar_cascade = cv2.CascadeClassifier(haar_path)
        print("  Face detector: OpenCV Haar Cascade (basic)")
        return "haar"

    @staticmethod
    def _download_yunet(path: Path):
        """Download YuNet face detection model."""
        import urllib.request
        url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
        try:
            print(f"  Downloading YuNet face detector...")
            path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, path)
            print(f"  -> saved ({path.stat().st_size / 1024:.0f} KB)")
        except Exception as e:
            print(f"  -> download failed: {e}")

    # ----- Object detection -----

    async def detect_objects(self, img: np.ndarray) -> list[dict]:
        """YOLOv8 object detection -> standardised participant list."""
        if self._yolo_detect is None:
            return []
        results = self._yolo_detect(img, verbose=False)[0]
        participants = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names[cls_id]
            x1, y1, x2, y2 = box.xyxyn[0].tolist()
            participants.append({
                "label": label,
                "confidence": float(box.conf[0]),
                "bbox": [x1, y1, x2, y2],
                "is_human": label == "person",
                "is_animal": label in (
                    "cat", "dog", "horse", "bird", "cow",
                    "sheep", "elephant", "bear", "zebra", "giraffe",
                ),
            })
        return participants

    async def detect_persons(self, img: np.ndarray) -> list[dict]:
        """YOLOv8-pose: full body bboxes + 17 COCO keypoints."""
        if self._yolo_pose is None:
            return []
        results = self._yolo_pose(img, verbose=False)[0]
        persons = []
        for i, box in enumerate(results.boxes):
            if int(box.cls[0]) != 0:
                continue
            x1, y1, x2, y2 = box.xyxyn[0].tolist()
            kpts = results.keypoints[i].xyn[0].tolist() if results.keypoints else None
            persons.append({
                "person_id": i,
                "bbox": [x1, y1, x2, y2],
                "keypoints": kpts,
                "confidence": float(box.conf[0]),
            })
        return persons

    # ----- Face detection (multi-backend) -----

    async def detect_faces(self, img_rgb: np.ndarray) -> list[dict]:
        """Detect faces using the best available backend."""
        if self._face_detector == "mediapipe":
            return self._detect_faces_mediapipe(img_rgb)
        elif self._face_detector == "yunet":
            return self._detect_faces_yunet(img_rgb)
        elif self._face_detector == "haar":
            return self._detect_faces_haar(img_rgb)
        return []

    def _detect_faces_mediapipe(self, img_rgb: np.ndarray) -> list[dict]:
        """MediaPipe Face Mesh: 468 landmarks, gaze, head pose."""
        if self._face_mesh is None:
            return []
        results = self._face_mesh.process(img_rgb)
        faces = []
        if not results.multi_face_landmarks:
            return faces

        h, w = img_rgb.shape[:2]
        for i, face_lm in enumerate(results.multi_face_landmarks):
            xs = [lm.x for lm in face_lm.landmark]
            ys = [lm.y for lm in face_lm.landmark]
            face_bbox = [min(xs), min(ys), max(xs), max(ys)]

            pan, tilt, roll = _estimate_head_pose_mediapipe(face_lm.landmark, w, h)
            emotions = self._predict_emotions(img_rgb, face_bbox, w, h)

            faces.append({
                "face_id": i,
                "face_bbox": face_bbox,
                "pan_angle": pan,
                "tilt_angle": tilt,
                "roll_angle": roll,
                "gaze_type": "demand" if abs(pan) < 15 and abs(tilt) < 15 else "offer",
                "emotions": emotions,
            })
        return faces

    def _detect_faces_yunet(self, img_rgb: np.ndarray) -> list[dict]:
        """OpenCV YuNet DNN face detector with 5-point landmarks."""
        if self._yunet is None:
            return []

        h, w = img_rgb.shape[:2]
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        # YuNet needs specific input size
        self._yunet.setInputSize((w, h))
        _, raw_faces = self._yunet.detect(img_bgr)

        if raw_faces is None:
            return []

        faces = []
        for i, face_data in enumerate(raw_faces):
            # YuNet output: [x, y, w, h, x_re, y_re, x_le, y_le, x_nt, y_nt, x_rm, y_rm, x_lm, y_lm, score]
            fx, fy, fw, fh = face_data[0:4].astype(int)
            score = float(face_data[14])

            if score < 0.5:
                continue

            # Normalise bbox to [0, 1]
            face_bbox = [fx / w, fy / h, (fx + fw) / w, (fy + fh) / h]

            # 5 landmarks: right_eye, left_eye, nose_tip, right_mouth, left_mouth
            right_eye = (float(face_data[4]), float(face_data[5]))
            left_eye = (float(face_data[6]), float(face_data[7]))
            nose = (float(face_data[8]), float(face_data[9]))

            # Estimate head pose from landmarks
            pan, tilt, roll = _estimate_head_pose_5pt(
                right_eye, left_eye, nose, fx, fy, fw, fh, w, h
            )

            emotions = self._predict_emotions(img_rgb, face_bbox, w, h)

            faces.append({
                "face_id": i,
                "face_bbox": face_bbox,
                "pan_angle": pan,
                "tilt_angle": tilt,
                "roll_angle": roll,
                "gaze_type": "demand" if abs(pan) < 15 and abs(tilt) < 15 else "offer",
                "emotions": emotions,
            })
        return faces

    def _detect_faces_haar(self, img_rgb: np.ndarray) -> list[dict]:
        """OpenCV Haar Cascade: basic face detection, approximate pose."""
        if self._haar_cascade is None:
            return []

        h, w = img_rgb.shape[:2]
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        gray = cv2.equalizeHist(gray)

        raw_faces = self._haar_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(int(w * 0.03), int(h * 0.03)),
        )

        faces = []
        for i, (fx, fy, fw, fh) in enumerate(raw_faces):
            face_bbox = [fx / w, fy / h, (fx + fw) / w, (fy + fh) / h]

            # Approximate gaze: assume direct gaze for frontal faces
            # (Haar only detects frontal faces anyway)
            face_cx = (fx + fw / 2) / w
            face_cy = (fy + fh / 2) / h

            # Simple heuristic: face near centre = demand, off-centre = offer
            pan = (face_cx - 0.5) * 60   # rough horizontal angle
            tilt = (face_cy - 0.5) * 40  # rough vertical angle

            emotions = self._predict_emotions(img_rgb, face_bbox, w, h)

            faces.append({
                "face_id": i,
                "face_bbox": face_bbox,
                "pan_angle": round(pan, 2),
                "tilt_angle": round(tilt, 2),
                "roll_angle": 0.0,
                "gaze_type": "demand" if abs(pan) < 15 and abs(tilt) < 15 else "offer",
                "emotions": emotions,
            })
        return faces

    # ----- Emotion recognition -----

    def _predict_emotions(self, img_rgb: np.ndarray, face_bbox, w, h) -> dict:
        """FER+ emotion recognition on cropped face."""
        if self._emotion_session is None:
            return {}
        x1, y1, x2, y2 = [int(v * d) for v, d in zip(face_bbox, [w, h, w, h])]
        # Expand crop slightly for better recognition
        pad_x = int((x2 - x1) * 0.1)
        pad_y = int((y2 - y1) * 0.1)
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(w, x2 + pad_x)
        y2 = min(h, y2 + pad_y)

        face_crop = img_rgb[y1:y2, x1:x2]
        if face_crop.size == 0:
            return {}
        face_gray = cv2.cvtColor(cv2.resize(face_crop, (64, 64)), cv2.COLOR_RGB2GRAY)
        input_tensor = face_gray.astype(np.float32).reshape(1, 1, 64, 64)
        try:
            probs = self._emotion_session.run(None, {"Input3": input_tensor})[0][0]
            probs = np.exp(probs) / np.exp(probs).sum()
            labels = ["neutral", "happiness", "surprise", "sadness",
                      "anger", "disgust", "fear", "contempt"]
            return {l: round(float(p), 4) for l, p in zip(labels, probs)}
        except Exception:
            return {}


# ----- Head pose estimation helpers -----

def _estimate_head_pose_mediapipe(landmarks, img_w, img_h):
    """Estimate pan/tilt/roll from MediaPipe 468 landmarks using solvePnP."""
    model_points = np.array([
        (0.0, 0.0, 0.0),        # nose tip
        (0.0, -330.0, -65.0),   # chin
        (-225.0, 170.0, -135.0), # left eye corner
        (225.0, 170.0, -135.0),  # right eye corner
        (-150.0, -150.0, -125.0),# left mouth corner
        (150.0, -150.0, -125.0), # right mouth corner
    ], dtype=np.float64)

    indices = [1, 152, 33, 263, 61, 291]
    image_points = np.array(
        [(landmarks[i].x * img_w, landmarks[i].y * img_h) for i in indices],
        dtype=np.float64,
    )
    focal_length = img_w
    camera_matrix = np.array(
        [[focal_length, 0, img_w / 2], [0, focal_length, img_h / 2], [0, 0, 1]],
        dtype=np.float64,
    )
    _, rotation_vec, _ = cv2.solvePnP(
        model_points, image_points, camera_matrix, np.zeros((4, 1))
    )
    rotation_mat, _ = cv2.Rodrigues(rotation_vec)
    angles = cv2.decomposeProjectionMatrix(np.hstack((rotation_mat, np.zeros((3, 1)))))[6]
    return float(angles[1, 0]), float(angles[0, 0]), float(angles[2, 0])


def _estimate_head_pose_5pt(right_eye, left_eye, nose, fx, fy, fw, fh, img_w, img_h):
    """Estimate pan/tilt/roll from 5-point landmarks (YuNet output).

    Uses the relative position of eyes and nose within the face bbox
    to approximate head orientation.
    """
    # Face centre
    face_cx = fx + fw / 2
    face_cy = fy + fh / 2

    # Eye midpoint
    eye_mx = (right_eye[0] + left_eye[0]) / 2
    eye_my = (right_eye[1] + left_eye[1]) / 2

    # Pan (yaw): nose offset from face centre horizontally
    nose_offset_x = (nose[0] - face_cx) / fw
    pan = nose_offset_x * 60  # scale to approximate degrees

    # Tilt (pitch): nose vertical position relative to eyes
    nose_offset_y = (nose[1] - eye_my) / fh
    tilt = (nose_offset_y - 0.2) * 50  # 0.2 is typical eye-to-nose ratio

    # Roll: angle between eyes
    dx = left_eye[0] - right_eye[0]
    dy = left_eye[1] - right_eye[1]
    roll = np.degrees(np.arctan2(dy, dx)) if abs(dx) > 1 else 0.0

    return round(float(pan), 2), round(float(tilt), 2), round(float(roll), 2)
